from collections.abc import Sequence
from datetime import datetime, timedelta

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
    MensagemLLM,
    ProvedorLLM,
    ServicoIA,
)
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.conversa import responder_conversa


class ProviderFalso(ProvedorLLM):
    def __init__(self, texto: str = "resposta da IA") -> None:
        self.texto = texto
        self.chamadas: list[Sequence[MensagemLLM]] = []

    async def gerar_resposta(self, mensagens: Sequence[MensagemLLM]) -> str:
        self.chamadas.append(mensagens)
        return self.texto


def _empresa() -> Empresa:
    return Empresa(
        tenant_id="empresa-1",
        nome="Empresa 1",
        status=StatusEmpresa.ATIVA,
        telefone_notificacao="11999999999",
        configuracao_ia=ConfiguracaoIA(
            tom=TomDaIA.INFORMAL,
            pode_dizer_que_e_ia=True,
            nome_assistente="Ana",
            horario_atendimento_ia=Intervalo(
                horario_inicio=datetime(2026, 1, 1, 8, 0),
                horario_fim=datetime(2026, 1, 1, 18, 0),
            ),
        ),
        regras_gerais=[],
        cidades_atendidas=[],
        estagios=[],
    )


async def _criar_empresa() -> Empresa:
    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        empresa = await uow.dominio.salvar(_empresa())
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
        foi_enviada_pela_ia=False,
        foi_enviada_pelo_humano=False,
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
    assert resposta.foi_enviada_pela_ia is True
    assert resposta.foi_enviada_pelo_humano is False
    assert resposta.identificador_da_mensagem.startswith("ia:")
    assert len(provider.chamadas) == 1


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


async def test_responder_responde_mesmo_sem_ser_a_ultima_mensagem():
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

    assert gerou is True
    conversa = await _buscar_conversa()
    assert conversa is not None
    assert len(conversa.mensagens) == 3
    assert len(provider.chamadas) == 1


async def test_responder_ignora_mensagem_fora_da_janela_de_resposta():
    await _criar_empresa()
    await _criar_conversa(
        [_mensagem("msg-1", "oi", datetime.now() - timedelta(seconds=60))]
    )
    provider = ProviderFalso()

    gerou = await responder_conversa(
        "empresa-1", "11988887777", "msg-1", ServicoIA(provider)
    )

    assert gerou is False
    assert provider.chamadas == []


async def test_responder_envia_apenas_mensagens_da_janela_para_ia():
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
    assert len(provider.chamadas) == 1
    assert [mensagem.conteudo for mensagem in provider.chamadas[0][1:]] == ["recente"]


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
