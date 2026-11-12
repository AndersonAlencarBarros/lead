import time
from datetime import datetime

from config import get_settings
from dominio.agregados.conversa import Conversa
from dominio.agregados.empresa import Empresa
from dominio.agregados.lead import Lead
from dominio.agregados.turno_ia import StatusTurno, TurnoIA
from dominio.objetos_de_valor.conversa import (
    AcaoIntervencao,
    AutorMensagem,
    Mensagem,
    ResultadoMensagem,
)
from dominio.regras_de_negocio.conversa import (
    MENSAGEM_FORA_DO_HORARIO,
    _salvar_resposta_ia,
    _ultima_mensagem_do_usuario_sem_resposta,
    contexto_para_resposta_da_ia,
    historico_para_resposta_da_ia,
    idempotente_em_conflito,
    ultima_mensagem_de_intervencao_humana,
    ultima_resposta_da_ia,
)
from dominio.regras_de_negocio.servico_ia import ServicoIA
from exceptions import (
    ConversaNaoEncontrada,
    FilaDeProcessamentoIndisponivel,
    IntervencaoHumanaNaoEncontrada,
    RespostaDaIANaoEncontrada,
)
from infraestrutura import Dominio, UnidadeDeTrabalho
from repositorio.conversa import ConversaDominioRepositorio, ConversaLeituraRepositorio
from repositorio.lead import LeadDominioRepositorio, LeadLeituraRepositorio
from repositorio.turno_ia import TurnoDominioRepositorio, TurnoLeituraRepositorio
from servicos.executores.ferramentas import ExecutorFerramentas
from servicos.serializadores.conversacao import (
    IntervencaoSerializador,
    MensagemSerializador,
)
from servicos.visualizadores.conversa import (
    buscar_conversa_por_empresa_e_telefone,
)


@idempotente_em_conflito
async def receber_mensagem(
    mensagem: MensagemSerializador, uow: UnidadeDeTrabalho
) -> ResultadoMensagem:
    from dominio.regras_de_negocio.servico_ia.responder_conversa import (
        criar_resposta_da_ia,
    )

    repo_dominio: ConversaDominioRepositorio = uow.dominio
    repo_leitura: ConversaLeituraRepositorio = uow.leitura

    if await repo_leitura.mensagem_existe(mensagem.message_id):
        return ResultadoMensagem.DUPLICADA

    empresa = await repo_dominio.buscar_empresa_por_tenant_id(mensagem.tenant_id)
    atraso = empresa.janela_de_resposta if empresa is not None else 0

    # Busca se existe conversa
    conversa = await repo_leitura.buscar_por_empresa_e_telefone(
        mensagem.tenant_id, mensagem.telefone
    )
    if conversa is None:
        # Inicia-se uma conversa
        conversa = Conversa(
            tenant_id=mensagem.tenant_id,
            lead_id=None,
            telefone=mensagem.telefone,
        )

    if empresa is not None and conversa.lead_id is None:
        lead_repo = LeadDominioRepositorio(uow.session)
        lead_leitura = LeadLeituraRepositorio(uow.session)
        lead = await lead_leitura.buscar_por_empresa_e_telefone(
            empresa.id,
            mensagem.telefone,
        )
        if lead is None:
            from dominio.agregados.lead import Lead

            lead = Lead(
                empresa_id=empresa.id,
                telefone=mensagem.telefone,
            )
            lead = await lead_repo.salvar(lead)
        conversa.lead_id = lead.id

    eh_humano = mensagem.autor is AutorMensagem.HUMANO

    # Adiciona uma mensagem a conversa
    conversa.receber_mensagem(
        Mensagem(
            id=None,
            identificador_da_mensagem=mensagem.message_id,
            conversa_id=None,
            texto=mensagem.texto,
            foi_gerada_pela_ia=False,
            foi_respondida_pelo_usuario=not eh_humano,
            foi_intervencao_humana=eh_humano,
            simulacao=mensagem.simulacao,
            criado_em=datetime.now(),
        )
    )

    if eh_humano:
        conversa.ativar_intervencao_humana()

    await repo_dominio.salvar(conversa)
    await uow.commit()

    if conversa.ia_pode_responder():
        try:
            criar_resposta_da_ia(
                mensagem.tenant_id,
                mensagem.telefone,
                mensagem.message_id,
                atraso,
            )
        except Exception as exc:
            raise FilaDeProcessamentoIndisponivel() from exc

    return ResultadoMensagem.PROCESSADA


async def alterar_intervencao(
    payload: IntervencaoSerializador,
    uow: UnidadeDeTrabalho,
) -> Conversa:
    """Assume a conversa ou devolve o atendimento para a IA."""
    from dominio.regras_de_negocio.servico_ia.responder_conversa import (
        criar_resposta_da_ia,
    )

    repo_dominio: ConversaDominioRepositorio = uow.dominio
    repo_leitura: ConversaLeituraRepositorio = uow.leitura

    conversa = await repo_leitura.buscar_por_empresa_e_telefone(
        payload.tenant_id,
        payload.telefone,
    )
    if conversa is None:
        raise ConversaNaoEncontrada()

    if payload.acao is AcaoIntervencao.ASSUMIR:
        conversa.ativar_intervencao_humana()
        return await repo_dominio.salvar(conversa)

    conversa.desativar_intervencao_humana()
    await repo_dominio.salvar(conversa)
    await uow.commit()

    mensagem_pendente = _ultima_mensagem_do_usuario_sem_resposta(conversa)
    if mensagem_pendente is not None:
        try:
            criar_resposta_da_ia(
                conversa.tenant_id,
                str(conversa.telefone),
                mensagem_pendente.identificador_da_mensagem,
            )
        except Exception as exc:
            raise FilaDeProcessamentoIndisponivel() from exc

    return conversa


async def responder_ultima_mensagem_da_conversa(
    tenant_id: str,
    telefone: str,
    uow: UnidadeDeTrabalho,
) -> tuple[Conversa, Mensagem]:
    """Busca a conversa e a última mensagem relevante para o usuário."""
    conversa = await buscar_conversa_por_empresa_e_telefone(
        tenant_id,
        telefone,
        uow,
    )
    if conversa is None:
        raise ConversaNaoEncontrada()

    if conversa.teve_intervencao_humana:
        mensagem = ultima_mensagem_de_intervencao_humana(conversa)
        if mensagem is None:
            raise IntervencaoHumanaNaoEncontrada()
    else:
        mensagem = ultima_resposta_da_ia(conversa)
        if mensagem is None:
            raise RespostaDaIANaoEncontrada()

    return conversa, mensagem


async def responder_conversa(
    tenant_id: str,
    telefone: str,
    mensagem_id: str,
    servico_ia: ServicoIA,
    usar_ferramentas: bool = True,
) -> bool:
    """Gera e persiste a resposta da IA para a mensagem informada."""

    inicio = time.perf_counter()

    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        empresa: Empresa | None = await uow.dominio.buscar_empresa_por_tenant_id(
            tenant_id
        )
        if empresa is None or not empresa.esta_ativa():
            return False

        conversa = await uow.dominio.buscar_por_empresa_e_telefone(tenant_id, telefone)
        if conversa is None:
            return False

        mensagem_pendente = _ultima_mensagem_do_usuario_sem_resposta(conversa)
        if (
            mensagem_pendente is None
            or mensagem_pendente.identificador_da_mensagem != mensagem_id
        ):
            return False

        if not empresa.esta_em_horario_de_atendimento(datetime.now()):
            texto = MENSAGEM_FORA_DO_HORARIO.format(
                horario=empresa.configuracao_ia.horario_atendimento_ia.formatar()
            )
            return await _salvar_resposta_ia(
                conversa,
                mensagem_id,
                texto,
                uow,
            )

        lead = await _obter_ou_criar_lead(uow, empresa, conversa, telefone)
        if lead is None:
            return False

        mensagens_pendentes = contexto_para_resposta_da_ia(conversa)
        if mensagens_pendentes is None:
            return False

        mensagens_pendentes = [
            Mensagem(
                identificador_da_mensagem=mensagem.identificador_da_mensagem,
                texto=mensagem.texto,
                foi_gerada_pela_ia=mensagem.foi_gerada_pela_ia,
                foi_respondida_pelo_usuario=mensagem.foi_respondida_pelo_usuario,
                foi_intervencao_humana=mensagem.foi_intervencao_humana,
                simulacao=mensagem.simulacao,
                criado_em=mensagem.criado_em,
            )
            for mensagem in mensagens_pendentes
        ]
        historico = [
            Mensagem(
                identificador_da_mensagem=mensagem.identificador_da_mensagem,
                texto=mensagem.texto,
                foi_gerada_pela_ia=mensagem.foi_gerada_pela_ia,
                foi_respondida_pelo_usuario=mensagem.foi_respondida_pelo_usuario,
                foi_intervencao_humana=mensagem.foi_intervencao_humana,
                simulacao=mensagem.simulacao,
                criado_em=mensagem.criado_em,
            )
            for mensagem in historico_para_resposta_da_ia(conversa) or []
        ]

        turno_repo = TurnoDominioRepositorio(uow.session)
        turno_leitura = TurnoLeituraRepositorio(uow.session)
        turno = await turno_leitura.buscar_por_conversa_e_mensagem(
            conversa.id,
            mensagem_id,
        )
        if turno is None:
            turno = TurnoIA(
                conversa_id=conversa.id,
                tenant_id=tenant_id,
                mensagem_origem_id=mensagem_id,
            )
        else:
            turno.status = StatusTurno.EM_ANDAMENTO
            turno.erro = None
        turno = await turno_repo.salvar(turno)
        await uow.commit()

        conversa_id = conversa.id
        lead_id = lead.id
        simulacao = mensagem_pendente.simulacao

    executor = ExecutorFerramentas(
        empresa=empresa,
        conversa_id=conversa_id,
        lead_id=lead_id,
        simulacao=simulacao,
        turno=turno,
    )

    try:
        resultado = await servico_ia.responder(
            historico,
            empresa,
            lead=lead,
            executar_ferramenta=executor.executar if usar_ferramentas else None,
        )
    except Exception as exc:
        await _marcar_turno_como_falho(turno.id, str(exc))
        raise

    latencia_ms = int((time.perf_counter() - inicio) * 1000)
    settings = get_settings()
    custo = (
        resultado.tokens_entrada / 1_000_000 * settings.llm_preco_entrada_por_milhao
        + resultado.tokens_saida / 1_000_000 * settings.llm_preco_saida_por_milhao
    )

    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        conversa = await ConversaLeituraRepositorio(uow.session).buscar_por_id(
            conversa_id
        )
        transferiu = any(
            acao["ferramenta"] == "transferir_humano" and acao["sucesso"]
            for acao in resultado.acoes
        )
        if conversa is None or (not conversa.ia_pode_responder() and not transferiu):
            return False

        mensagem_pendente = _ultima_mensagem_do_usuario_sem_resposta(conversa)
        if (
            mensagem_pendente is None
            or mensagem_pendente.identificador_da_mensagem != mensagem_id
        ):
            return False

        salvo = await _salvar_resposta_ia(
            conversa,
            mensagem_id,
            resultado.texto,
            uow,
        )
        if not salvo:
            return False

        turno = await TurnoLeituraRepositorio(uow.session).buscar_por_id(turno.id)
        if turno is not None:
            turno.concluir(
                modelo=resultado.modelo,
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
                custo_estimado=custo,
                latencia_ms=latencia_ms,
            )
            await TurnoDominioRepositorio(uow.session).salvar(turno)

        await uow.commit()
        return True


async def _obter_ou_criar_lead(
    uow: UnidadeDeTrabalho,
    empresa: Empresa,
    conversa: Conversa,
    telefone: str,
) -> Lead | None:
    if conversa.lead_id is not None:
        return await LeadLeituraRepositorio(uow.session).buscar_por_id(conversa.lead_id)

    lead_repo = LeadDominioRepositorio(uow.session)
    lead = await LeadLeituraRepositorio(uow.session).buscar_por_empresa_e_telefone(
        empresa.id,
        telefone,
    )
    if lead is None:
        lead = Lead(empresa_id=empresa.id, telefone=telefone)
        lead = await lead_repo.salvar(lead)

    conversa.lead_id = lead.id
    await ConversaDominioRepositorio(uow.session).salvar(conversa)
    return lead


async def _marcar_turno_como_falho(turno_id, erro: str) -> None:
    async with UnidadeDeTrabalho(Dominio.TURNO) as uow:
        turno = await uow.leitura.buscar_por_id(turno_id)
        if turno is None:
            return
        turno.falhar(erro[:500])
        await uow.dominio.salvar(turno)
        await uow.commit()
