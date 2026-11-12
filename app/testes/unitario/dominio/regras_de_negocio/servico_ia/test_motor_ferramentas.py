from datetime import datetime

from dominio.agregados.empresa import Empresa
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
    construir_ferramentas,
)
from exceptions import FalhaAoConsultarIA
from testes.apoio import playbook_confeitaria, playbook_solar


class ProvedorRoteirizado(ProvedorLLM):
    def __init__(self, respostas: list[RespostaLLM]) -> None:
        self.respostas = list(respostas)
        self.contextos: list[list[dict]] = []

    async def gerar_resposta(self, mensagens, ferramentas):
        self.contextos.append([dict(mensagem) for mensagem in mensagens])
        return self.respostas.pop(0)


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
                horario_inicio=datetime(2026, 1, 1, 0, 0),
                horario_fim=datetime(2026, 1, 1, 23, 59),
            ),
        ),
        regras_gerais=[],
        cidades_atendidas=["Recife"],
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


def _resposta(
    texto: str | None = None,
    chamadas: tuple[ChamadaFerramenta, ...] = (),
) -> RespostaLLM:
    return RespostaLLM(
        conteudo=texto,
        chamadas=chamadas,
        modelo="fake",
        tokens_entrada=1,
        tokens_saida=1,
    )


async def test_consultar_agenda_volta_ao_modelo_antes_da_resposta():
    provedor = ProvedorRoteirizado(
        [
            _resposta(
                chamadas=(
                    ChamadaFerramenta(
                        id="call-1",
                        nome="consultar_agenda",
                        argumentos={},
                    ),
                    ChamadaFerramenta(
                        id="call-2",
                        nome="adicionar_tag",
                        argumentos={"tag": "em-atendimento"},
                    ),
                    ChamadaFerramenta(
                        id="call-3",
                        nome="mover_estagio",
                        argumentos={"estagio": "Qualificacao"},
                    ),
                )
            ),
            _resposta("Tenho quinta às 09h. Pode ser?"),
        ]
    )
    executadas: list[str] = []

    async def executar(chamada):
        executadas.append(chamada.nome)
        return {"horarios": ["2026-11-12T09:00:00"]}

    resultado = await ServicoIA(provedor).responder(
        [],
        _empresa(),
        executar_ferramenta=executar,
    )

    assert executadas == [
        "consultar_agenda",
        "adicionar_tag",
        "mover_estagio",
    ]
    assert resultado.texto == "Tenho quinta às 09h. Pode ser?"
    assert provedor.contextos[1][-1]["role"] == "tool"
    assert "2026-11-12T09:00:00" in provedor.contextos[1][-1]["content"]


async def test_turno_sem_tag_e_estagio_recebe_correcao():
    provedor = ProvedorRoteirizado(
        [
            _resposta("Olá, como posso ajudar?"),
            _resposta(
                chamadas=(
                    ChamadaFerramenta(
                        id="call-1",
                        nome="adicionar_tag",
                        argumentos={"tag": "em-atendimento"},
                    ),
                    ChamadaFerramenta(
                        id="call-2",
                        nome="mover_estagio",
                        argumentos={"estagio": "Qualificacao"},
                    ),
                )
            ),
            _resposta("Pode me dizer seu nome e cidade?"),
        ]
    )

    async def executar(chamada):
        return {"ok": True}

    resultado = await ServicoIA(provedor).responder(
        [],
        _empresa(),
        executar_ferramenta=executar,
    )

    assert resultado.iteracoes == 3
    assert len(resultado.acoes) == 2
    assert resultado.texto == "Pode me dizer seu nome e cidade?"
    assert any(
        "sem executar adicionar_tag" in (mensagem["content"] or "")
        for mensagem in provedor.contextos[1]
    )


async def test_chamada_de_ferramenta_sem_executor_falha():
    provedor = ProvedorRoteirizado(
        [
            _resposta(
                chamadas=(
                    ChamadaFerramenta(
                        id="call-1",
                        nome="consultar_agenda",
                        argumentos={},
                    ),
                )
            )
        ]
    )

    try:
        await ServicoIA(provedor).responder([], _empresa())
    except FalhaAoConsultarIA:
        pass
    else:
        raise AssertionError("esperava FalhaAoConsultarIA")


async def test_tool_call_json_em_texto_e_recuperada():
    provedor = ProvedorRoteirizado(
        [
            _resposta('{"name": "consultar_agenda", "arguments": {}}'),
            _resposta(
                chamadas=(
                    ChamadaFerramenta(
                        id="tag",
                        nome="adicionar_tag",
                        argumentos={"tag": "em-atendimento"},
                    ),
                    ChamadaFerramenta(
                        id="estagio",
                        nome="mover_estagio",
                        argumentos={"estagio": "Qualificacao"},
                    ),
                )
            ),
            _resposta("Tenho quinta às 09h. Pode ser?"),
        ]
    )
    executadas: list[str] = []

    async def executar(chamada):
        executadas.append(chamada.nome)
        if chamada.nome == "consultar_agenda":
            return {"horarios": ["2026-11-12T09:00:00"]}
        return {"ok": True}

    resultado = await ServicoIA(provedor).responder(
        [],
        _empresa(),
        executar_ferramenta=executar,
    )

    assert executadas == [
        "consultar_agenda",
        "adicionar_tag",
        "mover_estagio",
    ]
    assert resultado.texto == "Tenho quinta às 09h. Pode ser?"
    assert provedor.contextos[1][-1]["role"] == "tool"


async def test_json_final_com_tag_e_estagio_nao_e_aceito():
    provedor = ProvedorRoteirizado(
        [
            _resposta(
                chamadas=(
                    ChamadaFerramenta(
                        id="tag",
                        nome="adicionar_tag",
                        argumentos={"tag": "em-atendimento"},
                    ),
                    ChamadaFerramenta(
                        id="estagio",
                        nome="mover_estagio",
                        argumentos={"estagio": "Qualificacao"},
                    ),
                )
            ),
            _resposta('{"name": "consultar_agenda"}'),
            _resposta("Vou verificar os horários para você."),
        ]
    )
    executadas: list[str] = []

    async def executar(chamada):
        executadas.append(chamada.nome)
        return {"horarios": []}

    resultado = await ServicoIA(provedor).responder(
        [],
        _empresa(),
        executar_ferramenta=executar,
    )

    assert executadas[-1] == "consultar_agenda"
    assert not resultado.texto.startswith("{")


async def test_json_sem_ferramenta_conhecida_recebe_correcao():
    provedor = ProvedorRoteirizado(
        [
            _resposta('{"foo": "bar"}'),
            _resposta(
                chamadas=(
                    ChamadaFerramenta(
                        id="tag",
                        nome="adicionar_tag",
                        argumentos={"tag": "em-atendimento"},
                    ),
                    ChamadaFerramenta(
                        id="estagio",
                        nome="mover_estagio",
                        argumentos={"estagio": "Qualificacao"},
                    ),
                )
            ),
            _resposta("Pode me dizer seu nome?"),
        ]
    )

    async def executar(chamada):
        return {"ok": True}

    resultado = await ServicoIA(provedor).responder(
        [],
        _empresa(),
        executar_ferramenta=executar,
    )

    assert resultado.iteracoes == 3
    assert resultado.texto == "Pode me dizer seu nome?"


def test_ferramentas_seguem_playbook_do_tenant():
    empresa = _empresa()
    empresa.configuracoes.playbook = playbook_confeitaria()
    ferramentas = construir_ferramentas(empresa)
    atualizar = next(
        ferramenta
        for ferramenta in ferramentas
        if ferramenta["function"]["name"] == "atualizar_ficha"
    )
    campos = atualizar["function"]["parameters"]["properties"]["campo"]["enum"]

    assert "produto" in campos
    assert "imovel" not in campos
