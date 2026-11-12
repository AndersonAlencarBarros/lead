from datetime import datetime, timedelta

import pytest

from dominio.agregados.conversa import Conversa
from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.conversa import Mensagem
from dominio.objetos_de_valor.empresa import (
    ConfiguracaoIA,
    Intervalo,
    StatusEmpresa,
    TomDaIA,
)
from dominio.regras_de_negocio.servico_ia import (
    ChamadaFerramenta,
    ProvedorLLM,
    RespostaLLM,
    ServicoIA,
)
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.conversa import responder_conversa
from testes.apoio import playbook_solar


class ProviderFalso(ProvedorLLM):
    def __init__(self, texto: str = "resposta da IA") -> None:
        self.texto = texto
        self.chamadas: list[tuple[dict, ...]] = []
        self.turnos = 0

    async def gerar_resposta(
        self,
        mensagens,
        ferramentas=(),
    ) -> RespostaLLM:
        self.chamadas.append(tuple(dict(mensagem) for mensagem in mensagens))
        self.turnos += 1
        if self.turnos == 1:
            return RespostaLLM(
                conteudo=None,
                chamadas=(
                    ChamadaFerramenta(
                        id="tool-1",
                        nome="adicionar_tag",
                        argumentos={"tag": "em-atendimento"},
                    ),
                    ChamadaFerramenta(
                        id="tool-2",
                        nome="mover_estagio",
                        argumentos={"estagio": "Qualificacao"},
                    ),
                ),
                modelo="fake",
                tokens_entrada=1,
                tokens_saida=1,
            )
        return RespostaLLM(
            conteudo=self.texto,
            chamadas=(),
            modelo="fake",
            tokens_entrada=1,
            tokens_saida=1,
        )


def _empresa(
    status: StatusEmpresa = StatusEmpresa.ATIVA,
    inicio: datetime | None = None,
    fim: datetime | None = None,
) -> Empresa:
    agora = datetime.now()
    return Empresa(
        tenant_id="empresa-1",
        nome="Empresa 1",
        status=status,
        telefone_notificacao="11999999999",
        configuracao_ia=ConfiguracaoIA(
            tom=TomDaIA.INFORMAL,
            pode_dizer_que_e_ia=True,
            nome_assistente="Ana",
            horario_atendimento_ia=Intervalo(
                horario_inicio=inicio
                or agora.replace(hour=0, minute=0, second=0, microsecond=0),
                horario_fim=fim
                or agora.replace(hour=23, minute=59, second=59, microsecond=999999),
            ),
        ),
        regras_gerais=[],
        cidades_atendidas=[],
        estagios=[
            "Novo",
            "Qualificacao",
            "Qualificado",
            "Desqualificado",
            "Agendado",
            "Humano",
        ],
        playbook=playbook_solar(),
    )


def _janela_fora_do_horario() -> tuple[datetime, datetime]:
    inicio = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(
        hours=12
    )
    return inicio, inicio + timedelta(hours=1)


async def _criar_empresa(
    status: StatusEmpresa = StatusEmpresa.ATIVA,
    inicio: datetime | None = None,
    fim: datetime | None = None,
) -> Empresa:
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        empresa = await uow.dominio.salvar(_empresa(status, inicio, fim))
        await uow.commit()
    return empresa


async def _criar_conversa(mensagens: list[Mensagem]) -> Conversa:
    conversa = Conversa(
        tenant_id="empresa-1",
        telefone="11988887777",
        mensagens=mensagens,
        criado_em=datetime(2026, 1, 1, 9, 0),
    )
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        salva = await uow.dominio.salvar(conversa)
        await uow.commit()
    return salva


def _mensagem(
    identificador: str,
    texto: str,
    horario: datetime,
) -> Mensagem:
    return Mensagem(
        identificador_da_mensagem=identificador,
        texto=texto,
        foi_gerada_pela_ia=False,
        foi_respondida_pelo_usuario=True,
        criado_em=horario,
    )


def _mensagem_humana(
    identificador: str,
    texto: str,
    horario: datetime,
) -> Mensagem:
    return Mensagem(
        identificador_da_mensagem=identificador,
        texto=texto,
        foi_gerada_pela_ia=False,
        foi_respondida_pelo_usuario=False,
        foi_intervencao_humana=True,
        criado_em=horario,
    )


async def _buscar_conversa() -> Conversa | None:
    async with UnidadeDeTrabalho(Dominio.CONVERSA) as uow:
        return await uow.leitura.buscar_por_empresa_e_telefone(
            "empresa-1", "11988887777"
        )


async def test_responder_persiste_resposta_da_ia():
    await _criar_empresa()
    await _criar_conversa([_mensagem("msg-1", "oi", datetime.now())])
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1",
        "11988887777",
        "msg-1",
        ServicoIA(provider),
    )

    assert gerou is True
    conversa = await _buscar_conversa()
    assert conversa is not None
    assert conversa.mensagens[0].identificador_da_mensagem == "msg-1"
    resposta = conversa.mensagens[-1]
    assert resposta.texto == "resposta da IA"
    assert resposta.foi_gerada_pela_ia is True
    assert resposta.foi_respondida_pelo_usuario is False
    assert resposta.identificador_da_mensagem.startswith("ia:")
    assert len(provider.chamadas) == 2


async def test_responder_nao_duplica_resposta():
    await _criar_empresa()
    await _criar_conversa([_mensagem("msg-1", "oi", datetime.now())])
    provider = ProviderFalso()

    primeira = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(provider)
    )
    segunda = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(provider)
    )

    assert primeira is True
    assert segunda is False
    conversa = await _buscar_conversa()
    assert conversa is not None
    assert len(conversa.mensagens) == 2
    assert len(provider.chamadas) == 2


async def test_responder_ignora_gatilho_antigo():
    await _criar_empresa()
    agora = datetime.now()
    await _criar_conversa(
        [
            _mensagem("msg-1", "primeira", agora - timedelta(seconds=2)),
            _mensagem("msg-2", "segunda", agora - timedelta(seconds=1)),
        ]
    )
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(provider)
    )

    assert gerou is False
    assert provider.chamadas == []
    conversa = await _buscar_conversa()
    assert conversa is not None
    assert len(conversa.mensagens) == 2


async def test_responder_processa_gatilho_antigo():
    await _criar_empresa()
    await _criar_conversa(
        [_mensagem("msg-1", "oi", datetime.now() - timedelta(seconds=60))]
    )
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(provider)
    )

    assert gerou is True
    assert len(provider.chamadas) == 2


async def test_responder_envia_mensagens_pendentes_para_ia():
    await _criar_empresa()
    agora = datetime.now()
    await _criar_conversa(
        [
            _mensagem("msg-antiga", "antiga", agora - timedelta(seconds=60)),
            _mensagem("msg-recente", "recente", agora),
        ]
    )
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1", "11988887777", "msg-recente", ServicoIA(provider)
    )

    assert gerou is True
    assert len(provider.chamadas) == 2
    assert [mensagem["content"] for mensagem in provider.chamadas[0][1:]] == [
        "antiga",
        "recente",
    ]


async def test_responder_rajada_usa_ultima_mensagem_como_gatilho():
    await _criar_empresa()
    agora = datetime.now()
    await _criar_conversa(
        [
            _mensagem("msg-1", "oi", agora - timedelta(seconds=3)),
            _mensagem(
                "msg-2",
                "quero energia solar",
                agora - timedelta(seconds=2),
            ),
            _mensagem(
                "msg-3",
                "me manda um orçamento",
                agora - timedelta(seconds=1),
            ),
        ]
    )
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1", "11988887777", "msg-3", ServicoIA(provider)
    )

    assert gerou is True
    assert len(provider.chamadas) == 2
    assert [mensagem["content"] for mensagem in provider.chamadas[0][1:]] == [
        "oi",
        "quero energia solar",
        "me manda um orçamento",
    ]


async def test_responder_inclui_intervencoes_humanas_fora_da_janela():
    await _criar_empresa()
    agora = datetime.now()
    await _criar_conversa(
        [
            _mensagem(
                "msg-lead",
                "mensagem do lead",
                agora - timedelta(seconds=120),
            ),
            _mensagem_humana(
                "msg-humano",
                "resposta humana",
                agora - timedelta(seconds=90),
            ),
        ]
    )
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1",
        "11988887777",
        "msg-lead",
        ServicoIA(provider),
    )

    assert gerou is True
    assert len(provider.chamadas) == 2
    contexto = provider.chamadas[0][1:]
    assert [mensagem["content"] for mensagem in contexto] == [
        "mensagem do lead",
        "resposta humana",
    ]
    assert [mensagem["role"] for mensagem in contexto] == ["user", "assistant"]


async def test_responder_sem_empresa_nao_gera_resposta():
    await _criar_conversa([_mensagem("msg-1", "oi", datetime.now())])
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(provider)
    )

    assert gerou is False
    conversa = await _buscar_conversa()
    assert conversa is not None
    assert len(conversa.mensagens) == 1
    assert provider.chamadas == []


async def test_responder_fora_do_horario_persiste_mensagem():
    inicio, fim = _janela_fora_do_horario()
    empresa = await _criar_empresa(inicio=inicio, fim=fim)
    await _criar_conversa([_mensagem("msg-1", "oi", datetime.now())])
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(provider)
    )

    assert gerou is True
    assert provider.chamadas == []
    conversa = await _buscar_conversa()
    assert conversa is not None
    resposta = conversa.mensagens[-1]
    assert resposta.foi_gerada_pela_ia is True
    assert "fora desse horário" in resposta.texto
    assert empresa.configuracao_ia.horario_atendimento_ia.formatar() in resposta.texto


async def test_responder_fora_do_horario_nao_duplica():
    inicio, fim = _janela_fora_do_horario()
    await _criar_empresa(inicio=inicio, fim=fim)
    await _criar_conversa([_mensagem("msg-1", "oi", datetime.now())])

    primeira = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(ProviderFalso())
    )
    segunda = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(ProviderFalso())
    )

    assert primeira is True
    assert segunda is False
    conversa = await _buscar_conversa()
    assert conversa is not None
    assert len(conversa.mensagens) == 2


@pytest.mark.parametrize("status", [StatusEmpresa.INATIVA, StatusEmpresa.SUSPENSA])
async def test_responder_empresa_inativa_nao_responde(status):
    await _criar_empresa(status=status)
    await _criar_conversa([_mensagem("msg-1", "oi", datetime.now())])
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(provider)
    )

    assert gerou is False
    assert provider.chamadas == []
    conversa = await _buscar_conversa()
    assert conversa is not None
    assert len(conversa.mensagens) == 1
