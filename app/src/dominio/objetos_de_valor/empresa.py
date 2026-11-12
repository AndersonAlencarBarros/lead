from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum, StrEnum

from dominio.objetos_de_valor.playbook import Playbook


class StatusEmpresa(str, Enum):
    ATIVA = "ativa"
    INATIVA = "inativa"
    SUSPENSA = "suspensa"


class TomDaIA(StrEnum):
    INFORMAL = "informal"
    FORMAL = "formal"


class Cidade(str): ...


class Telefone(str): ...


class RegrasGerais(str): ...


class Estagio(str): ...


@dataclass
class Intervalo:
    horario_inicio: datetime
    horario_fim: datetime

    def __post_init__(self):
        class HorarioInvalido(ValueError):
            """Horário de início posterior ou igual ao de fim."""

        if self.horario_inicio >= self.horario_fim:
            raise HorarioInvalido("Horário Inválido")

    def contem(self, agora: datetime) -> bool:
        """Verifica se a hora atual está dentro da janela diária."""
        hora = agora.time()
        return self.horario_inicio.time() <= hora <= self.horario_fim.time()

    def abrange_o_dia_inteiro(self) -> bool:
        return (
            self.horario_inicio.time() == time.min
            and self.horario_fim.time() >= time(23, 59)
        )

    def formatar(self) -> str:
        if self.abrange_o_dia_inteiro():
            return "24 horas por dia"
        return f"das {self.horario_inicio:%H:%M} às {self.horario_fim:%H:%M}"


@dataclass
class ConfiguracaoIA:
    tom: TomDaIA
    pode_dizer_que_e_ia: bool
    nome_assistente: str
    horario_atendimento_ia: Intervalo


@dataclass
class DadosEmpresa:
    configuracao_ia: ConfiguracaoIA
    regras_gerais: list[RegrasGerais]
    cidades_atendidas: list[Cidade]
    estagios: list[Estagio]
    playbook: Playbook
