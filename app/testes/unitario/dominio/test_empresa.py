from datetime import datetime

from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.empresa import (
    ConfiguracaoIA,
    Intervalo,
    StatusEmpresa,
    TomDaIA,
)


def _intervalo(inicio: datetime, fim: datetime) -> Intervalo:
    return Intervalo(horario_inicio=inicio, horario_fim=fim)


def _empresa(status: StatusEmpresa) -> Empresa:
    return Empresa(
        tenant_id="empresa-1",
        nome="Empresa 1",
        status=status,
        telefone_notificacao="11999999999",
        configuracao_ia=ConfiguracaoIA(
            tom=TomDaIA.INFORMAL,
            pode_dizer_que_e_ia=True,
            nome_assistente="Ana",
            horario_atendimento_ia=_intervalo(
                datetime(2026, 1, 1, 8, 0),
                datetime(2026, 1, 1, 18, 0),
            ),
        ),
        regras_gerais=[],
        cidades_atendidas=[],
        estagios=[],
    )


def test_intervalo_contem_dentro_e_fora_da_janela():
    intervalo = _intervalo(
        datetime(2026, 1, 1, 8, 0),
        datetime(2026, 1, 1, 18, 0),
    )

    assert intervalo.contem(datetime(2026, 11, 11, 8, 0)) is True
    assert intervalo.contem(datetime(2026, 11, 11, 12, 0)) is True
    assert intervalo.contem(datetime(2026, 11, 11, 18, 0)) is True
    assert intervalo.contem(datetime(2026, 11, 11, 7, 59)) is False
    assert intervalo.contem(datetime(2026, 11, 11, 18, 1)) is False


def test_intervalo_formata_horario_configurado():
    intervalo = _intervalo(
        datetime(2026, 1, 1, 8, 0),
        datetime(2026, 1, 1, 18, 0),
    )

    assert intervalo.formatar() == "das 08:00 às 18:00"


def test_intervalo_formata_dia_inteiro_como_24_horas():
    intervalo = _intervalo(
        datetime(2026, 1, 1, 0, 0),
        datetime(2026, 1, 1, 23, 59),
    )

    assert intervalo.formatar() == "24 horas por dia"


def test_empresa_ativa_dentro_do_horario_pode_atender():
    agora = datetime(2026, 11, 11, 12, 0)

    assert _empresa(StatusEmpresa.ATIVA).pode_atender(agora) is True


def test_empresa_inativa_nao_pode_atender():
    agora = datetime(2026, 11, 11, 12, 0)

    assert _empresa(StatusEmpresa.INATIVA).pode_atender(agora) is False


def test_empresa_suspensa_nao_pode_atender():
    agora = datetime(2026, 11, 11, 12, 0)

    assert _empresa(StatusEmpresa.SUSPENSA).pode_atender(agora) is False


def test_empresa_ativa_fora_do_horario_nao_pode_atender():
    agora = datetime(2026, 11, 11, 20, 0)

    assert _empresa(StatusEmpresa.ATIVA).pode_atender(agora) is False
