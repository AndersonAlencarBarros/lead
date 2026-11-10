
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MensagemSerializador(BaseModel):
    message_id: str
    empresa_id: str
    telefone: str
    texto: str
    timestamp: str


class MensagemResposta(BaseModel):
    id: int
    identificador_da_mensagem: str
    texto: str
    autor: str
    foi_enviada_pela_ia: bool
    foi_enviada_pelo_humano: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversaSerializador(BaseModel):
    id: int
    empresa_id: str
    lead_id: str
    teve_intervencao_humana: bool
    criado_em: datetime
    mensagens: list[MensagemResposta]

    model_config = ConfigDict(from_attributes=True)
