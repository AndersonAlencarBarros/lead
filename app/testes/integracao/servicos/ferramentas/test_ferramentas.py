from datetime import datetime

from dominio.agregados.conversa import Conversa
from dominio.agregados.turno_ia import TurnoIA
from dominio.objetos_de_valor.conversa import Mensagem
from dominio.regras_de_negocio.servico_ia import ChamadaFerramenta
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.empresa import criar_empresa
from servicos.executores.ferramentas import ExecutorFerramentas
from servicos.executores.lead import criar_lead
from servicos.serializadores.empresa import (
    EXEMPLO_PLAYBOOK_SOL_NASCENTE,
    EmpresaCriacaoSerializador,
)


def _chamada(nome: str, argumentos: dict) -> ChamadaFerramenta:
    return ChamadaFerramenta(id=nome, nome=nome, argumentos=argumentos)


def _empresa_payload() -> EmpresaCriacaoSerializador:
    return EmpresaCriacaoSerializador(
        tenant_id="empresa-1",
        nome="Empresa 1",
        status="ativa",
        telefone_notificacao="11999999999",
        configuracao_ia={
            "tom": "informal",
            "pode_dizer_que_e_ia": True,
            "nome_assistente": "Ana",
            "horario_atendimento_ia": {
                "horario_inicio": "2026-01-01T08:00:00",
                "horario_fim": "2026-01-01T18:00:00",
            },
        },
        regras_gerais=[],
        cidades_atendidas=["Recife", "Caruaru"],
        estagios=[
            "Novo",
            "Qualificacao",
            "Qualificado",
            "Desqualificado",
            "Agendado",
            "Humano",
        ],
        playbook=EXEMPLO_PLAYBOOK_SOL_NASCENTE,
    )


async def _criar_contexto(texto: str = "meu nome é João Pereira, de Caruaru"):
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        empresa = await criar_empresa(_empresa_payload(), uow)
        await uow.commit()

    async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
        lead = await criar_lead(
            empresa.id,
            uow,
            telefone="11988887777",
        )
        await uow.commit()

    mensagem = Mensagem(
        identificador_da_mensagem="msg-1",
        texto=texto,
        foi_gerada_pela_ia=False,
        foi_respondida_pelo_usuario=True,
        criado_em=datetime.now(),
    )
    conversa = Conversa(
        tenant_id=empresa.tenant_id,
        telefone="11988887777",
        lead_id=lead.id,
        mensagens=[mensagem],
    )
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        conversa = await uow.dominio.salvar(conversa)
        await uow.commit()

    async with UnidadeDeTrabalho(Dominio.TURNO) as uow:
        turno = await uow.dominio.salvar(
            TurnoIA(
                conversa_id=conversa.id,
                tenant_id=empresa.tenant_id,
                mensagem_origem_id="msg-1",
            )
        )
        await uow.commit()

    executor = ExecutorFerramentas(
        empresa=empresa,
        conversa_id=conversa.id,
        lead_id=lead.id,
        simulacao=False,
        turno=turno,
    )
    return empresa, lead, conversa, executor


async def _buscar_lead(lead_id):
    async with UnidadeDeTrabalho(Dominio.LEAD) as uow:
        return await uow.leitura.buscar_por_id(lead_id)


async def _buscar_conversa(conversa_id):
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        return await uow.leitura.buscar_por_id(conversa_id)


async def _listar_auditorias(turno_id):
    async with UnidadeDeTrabalho(Dominio.AUDITORIA) as uow:
        return await uow.leitura.listar_por_turno(turno_id)


async def test_mover_estagio():
    _, lead, _, executor = await _criar_contexto()

    estagio = await executor.executar(
        _chamada("mover_estagio", {"estagio": "Agendado"})
    )

    assert estagio["ok"] is True
    atualizado = await _buscar_lead(lead.id)
    assert atualizado.estagio == "Agendado"


async def test_atualizar_lead_salva_nome_e_cidade():
    _, lead, _, executor = await _criar_contexto()

    resultado = await executor.executar(
        _chamada(
            "atualizar_lead",
            {"nome": "João Pereira", "cidade": "Recife"},
        )
    )

    assert resultado["ok"] is True
    atualizado = await _buscar_lead(lead.id)
    assert atualizado.nome == "João Pereira"
    assert atualizado.cidade == "Recife"

    auditorias = await _listar_auditorias(executor._turno.id)
    assert [(auditoria.ferramenta, auditoria.sucesso) for auditoria in auditorias] == [
        ("atualizar_lead", True),
    ]


async def test_atualizar_lead_rejeita_argumentos_vazios():
    _, _, _, executor = await _criar_contexto()

    resultado = await executor.executar(_chamada("atualizar_lead", {}))

    assert resultado["erro"] == "argumento_invalido:nome_ou_cidade"


async def test_auditorias_ficam_registradas():
    _, _, _, executor = await _criar_contexto()

    await executor.executar(_chamada("mover_estagio", {"estagio": "Qualificado"}))
    await executor.executar(_chamada("mover_estagio", {"estagio": "X"}))
    auditorias = await _listar_auditorias(executor._turno.id)

    assert [(auditoria.ferramenta, auditoria.sucesso) for auditoria in auditorias] == [
        ("mover_estagio", True),
        ("mover_estagio", False),
    ]


async def test_estagio_invalido_nao_move():
    _, lead, _, executor = await _criar_contexto()

    resultado = await executor.executar(
        _chamada("mover_estagio", {"estagio": "Inexistente"})
    )

    assert resultado["erro"] == "estagio_nao_permitido"
    atualizado = await _buscar_lead(lead.id)
    assert atualizado.estagio is None


async def test_agenda_consulta_marca_e_nao_duplica():
    _, _, _, executor = await _criar_contexto()

    sem_consulta = await executor.executar(
        _chamada("marcar_agenda", {"horario": "2030-01-03T09:00:00"})
    )
    agenda = await executor.executar(_chamada("consultar_agenda", {}))
    horario = agenda["horarios"][0]
    marcado = await executor.executar(_chamada("marcar_agenda", {"horario": horario}))
    repetido = await executor.executar(_chamada("marcar_agenda", {"horario": horario}))

    assert sem_consulta["erro"] == "horario_nao_consultado"
    assert marcado["ok"] is True
    assert repetido["agendamento_id"] == marcado["agendamento_id"]


async def test_transferir_humano_ativa_intervencao():
    _, lead, conversa, executor = await _criar_contexto()

    resultado = await executor.executar(
        _chamada("transferir_humano", {"motivo": "lead já é cliente"})
    )

    assert resultado["ok"] is True
    assert (await _buscar_conversa(conversa.id)).teve_intervencao_humana is True
    assert (await _buscar_lead(lead.id)).estagio == "Humano"


async def test_notificar_equipe_registra_simulacao():
    _, _, _, executor = await _criar_contexto()
    executor._simulacao = True

    resultado = await executor.executar(
        _chamada("notificar_equipe", {"resumo": "Lead qualificado"})
    )

    assert resultado["ok"] is True
    assert resultado["simulada"] is True
    assert resultado["telefone"] == "11999999999"
