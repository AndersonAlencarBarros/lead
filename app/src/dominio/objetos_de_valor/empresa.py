from dataclasses import dataclass
from datetime import datetime
from enum import Enum, StrEnum


class StatusEmpresa(str, Enum):
    ATIVA = "ativa"
    INATIVA = "inativa"
    SUSPENSA = "suspensa"


class TomDaIA(StrEnum):
    INFORMAL = "informal"
    FORMAL = "formal"


class HorarioInvalido(ValueError):
    """Horário de início posterior ou igual ao de fim."""


class Intervalo:
    horario_inicio: datetime
    horario_fim: datetime

    def __post_init__(self):
        if self.horario_inicio >= self.horario_fim:
            raise HorarioInvalido("Horário Inválido")


class Cidade(str): ...


class Telefone(str): ...


class RegrasGerais(str): ...


class Estagio(str): ...


@dataclass
class ConfiguracaoIA:
    tom: TomDaIA
    pode_dizer_que_e_ia: bool
    nome_assistente: str
    horario_atendimento_ia: Intervalo
