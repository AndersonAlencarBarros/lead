from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


@dataclass
class Mensagem:
    identificador_da_mensagem: str
    texto: str
    foi_gerada_pela_ia: bool
    foi_respondida_pelo_usuario: bool
    criado_em: datetime
    foi_intervencao_humana: bool = False
    simulacao: bool = False
    id: UUID | None = None
    conversa_id: UUID | None = None


class ResultadoMensagem(StrEnum):
    PROCESSADA = "processada"
    DUPLICADA = "duplicada"


class AcaoIntervencao(StrEnum):
    ASSUMIR = "assumir"
    RELIGAR = "religar"


class AutorMensagem(StrEnum):
    USUARIO = "usuario"  # usuário que envia mensagem
    HUMANO = "humano"  # colaborador da empresa que responde


class Telefone(str): ...
