from dataclasses import dataclass
from datetime import datetime


@dataclass
class Mensagem:
    id: int
    identificador_da_mensagem: str
    conversa_id: int
    texto: str
    autor: str
    foi_enviada_pela_ia: bool
    foi_enviada_pelo_humano: bool
    criado_em: datetime


class Telefone(str):
    ...
