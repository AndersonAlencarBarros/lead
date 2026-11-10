from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MensagemSerializador(BaseModel):
    message_id: str = Field(
        description="Identificador único da mensagem.",
        examples=["msg-123"],
    )
    tenant_id: str = Field(
        description="Identificador do tenant.",
        examples=["empresa-1"],
    )
    telefone: str = Field(
        description="Telefone do lead.",
        examples=["11999999999"],
    )
    texto: str = Field(
        description="Conteúdo da mensagem.",
        examples=["Olá, tenho interesse"],
    )
    timestamp: datetime = Field(description="Horário do evento no provedor.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message_id": "msg-123",
                    "tenant_id": "empresa-1",
                    "telefone": "11999999999",
                    "texto": "Olá, tenho interesse",
                    "timestamp": "2026-01-01T10:00:00",
                }
            ]
        }
    )


class MensagemResposta(BaseModel):
    id: UUID = Field(description="Identificador da mensagem.")
    identificador_da_mensagem: str = Field(
        description="Identificador externo da mensagem."
    )
    texto: str = Field(description="Conteúdo da mensagem.")
    foi_enviada_pela_ia: bool = Field(
        description="Indica se a mensagem foi enviada pela IA."
    )
    foi_enviada_pelo_humano: bool = Field(
        description="Indica se a mensagem foi enviada por um humano."
    )
    criado_em: datetime = Field(description="Data de criação da mensagem.")

    model_config = ConfigDict(from_attributes=True)


class ConversaSerializador(BaseModel):
    id: UUID = Field(description="Identificador da conversa.")
    tenant_id: str = Field(description="Identificador do tenant.")
    lead_id: UUID | None = Field(
        default=None,
        description="Identificador do lead, quando associado.",
    )
    teve_intervencao_humana: bool = Field(
        description="Indica se houve intervenção humana na conversa."
    )
    criado_em: datetime = Field(description="Data de criação da conversa.")
    mensagens: list[MensagemResposta] = Field(
        description="Mensagens da conversa em ordem cronológica."
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "tenant_id": "empresa-1",
                    "lead_id": None,
                    "teve_intervencao_humana": False,
                    "criado_em": "2026-01-01T09:00:00",
                    "mensagens": [
                        {
                            "id": "22222222-2222-2222-2222-222222222222",
                            "identificador_da_mensagem": "msg-123",
                            "texto": "Olá, tenho interesse",
                            "foi_enviada_pela_ia": False,
                            "foi_enviada_pelo_humano": False,
                            "criado_em": "2026-01-01T10:00:00",
                        }
                    ],
                }
            ]
        },
    )
