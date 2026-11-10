from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


@dataclass
class Mensagem:
    identificador_da_mensagem: str
    texto: str
    foi_enviada_pela_ia: bool
    foi_enviada_pelo_humano: bool
    criado_em: datetime
    id: UUID | None = None
    conversa_id: UUID | None = None


class ResultadoMensagem(StrEnum):
    PROCESSADA = "processada"
    DUPLICADA = "duplicada"


class Telefone(str): ...
