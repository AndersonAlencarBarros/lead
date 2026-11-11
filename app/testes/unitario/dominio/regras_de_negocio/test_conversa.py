from datetime import datetime, timedelta

from dominio.agregados.conversa import Conversa
from dominio.objetos_de_valor.conversa import Mensagem
from dominio.regras_de_negocio.conversa import (
    contexto_para_resposta_da_ia,
    ultima_resposta_da_ia,
)

AGORA = datetime(2026, 1, 1, 10, 0)


def _mensagem(
    identificador: str,
    horario: datetime,
    *,
    foi_gerada_pela_ia: bool,
) -> Mensagem:
    return Mensagem(
        identificador_da_mensagem=identificador,
        texto=identificador,
        foi_gerada_pela_ia=foi_gerada_pela_ia,
        foi_respondida_pelo_usuario=not foi_gerada_pela_ia,
        criado_em=horario,
    )


def _mensagem_humana(
    identificador: str,
    horario: datetime,
) -> Mensagem:
    return Mensagem(
        identificador_da_mensagem=identificador,
        texto=identificador,
        foi_gerada_pela_ia=False,
        foi_respondida_pelo_usuario=False,
        foi_intervencao_humana=True,
        criado_em=horario,
    )


def _conversa(
    mensagens: list[Mensagem],
    *,
    teve_intervencao_humana: bool = False,
) -> Conversa:
    conversa = Conversa(
        tenant_id="empresa-1",
        telefone="11999999999",
        mensagens=mensagens,
        criado_em=AGORA - timedelta(minutes=1),
    )
    conversa.teve_intervencao_humana = teve_intervencao_humana
    return conversa


def test_retorna_ultima_mensagem_gerada_pela_ia():
    conversa = _conversa(
        [
            _mensagem("lead-1", AGORA - timedelta(seconds=8), foi_gerada_pela_ia=False),
            _mensagem(
                "resposta-1", AGORA - timedelta(seconds=7), foi_gerada_pela_ia=True
            ),
            _mensagem("lead-2", AGORA - timedelta(seconds=2), foi_gerada_pela_ia=False),
            _mensagem("resposta-2", AGORA, foi_gerada_pela_ia=True),
        ]
    )

    resposta = ultima_resposta_da_ia(conversa)

    assert resposta is not None
    assert resposta.identificador_da_mensagem == "resposta-2"


def test_retorna_ultima_resposta_mesmo_com_mensagem_mais_recente_do_lead():
    conversa = _conversa(
        [
            _mensagem("lead-1", AGORA - timedelta(seconds=3), foi_gerada_pela_ia=False),
            _mensagem(
                "resposta-1", AGORA - timedelta(seconds=2), foi_gerada_pela_ia=True
            ),
            _mensagem("lead-2", AGORA, foi_gerada_pela_ia=False),
        ]
    )

    resposta = ultima_resposta_da_ia(conversa)

    assert resposta is not None
    assert resposta.identificador_da_mensagem == "resposta-1"


def test_retorna_none_quando_nao_ha_resposta_da_ia():
    conversa = _conversa([_mensagem("lead-1", AGORA, foi_gerada_pela_ia=False)])

    resposta = ultima_resposta_da_ia(conversa)

    assert resposta is None


def test_contexto_retorna_mensagem_pendente():
    agora = datetime.now()
    conversa = _conversa(
        [
            _mensagem(
                "lead-antigo",
                agora - timedelta(seconds=60),
                foi_gerada_pela_ia=False,
            )
        ]
    )

    contexto = contexto_para_resposta_da_ia(conversa)

    assert contexto is not None
    assert [mensagem.identificador_da_mensagem for mensagem in contexto] == [
        "lead-antigo"
    ]


def test_contexto_inclui_rajada_pendente():
    agora = datetime.now()
    conversa = _conversa(
        [
            _mensagem(
                "lead-1",
                agora - timedelta(seconds=3),
                foi_gerada_pela_ia=False,
            ),
            _mensagem(
                "lead-2",
                agora - timedelta(seconds=2),
                foi_gerada_pela_ia=False,
            ),
            _mensagem(
                "lead-3",
                agora - timedelta(seconds=1),
                foi_gerada_pela_ia=False,
            ),
        ]
    )

    contexto = contexto_para_resposta_da_ia(conversa)

    assert contexto is not None
    assert [mensagem.identificador_da_mensagem for mensagem in contexto] == [
        "lead-1",
        "lead-2",
        "lead-3",
    ]


def test_contexto_inclui_apenas_mensagens_apos_ultima_resposta_da_ia():
    agora = datetime.now()
    conversa = _conversa(
        [
            _mensagem(
                "lead-1",
                agora - timedelta(seconds=4),
                foi_gerada_pela_ia=False,
            ),
            _mensagem(
                "ia-1",
                agora - timedelta(seconds=3),
                foi_gerada_pela_ia=True,
            ),
            _mensagem(
                "lead-2",
                agora - timedelta(seconds=2),
                foi_gerada_pela_ia=False,
            ),
            _mensagem(
                "lead-3",
                agora - timedelta(seconds=1),
                foi_gerada_pela_ia=False,
            ),
        ]
    )

    contexto = contexto_para_resposta_da_ia(conversa)

    assert contexto is not None
    assert [mensagem.identificador_da_mensagem for mensagem in contexto] == [
        "lead-2",
        "lead-3",
    ]


def test_contexto_retorna_none_sem_mensagens_pendentes():
    agora = datetime.now()
    conversa = _conversa(
        [
            _mensagem(
                "lead",
                agora - timedelta(seconds=2),
                foi_gerada_pela_ia=False,
            ),
            _mensagem(
                "ia",
                agora - timedelta(seconds=1),
                foi_gerada_pela_ia=True,
            ),
        ]
    )

    contexto = contexto_para_resposta_da_ia(conversa)

    assert contexto is None


def test_contexto_inclui_intervencoes_humanas():
    agora = datetime.now()
    conversa = _conversa(
        [
            _mensagem(
                "lead",
                agora - timedelta(seconds=120),
                foi_gerada_pela_ia=False,
            ),
            _mensagem_humana("humano", agora - timedelta(seconds=90)),
        ]
    )

    contexto = contexto_para_resposta_da_ia(conversa)

    assert contexto is not None
    assert [mensagem.identificador_da_mensagem for mensagem in contexto] == [
        "lead",
        "humano",
    ]


def test_contexto_retorna_none_durante_intervencao():
    conversa = _conversa(
        [_mensagem("lead", datetime.now(), foi_gerada_pela_ia=False)],
        teve_intervencao_humana=True,
    )

    contexto = contexto_para_resposta_da_ia(conversa)

    assert contexto is None
