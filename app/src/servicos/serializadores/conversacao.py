from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dominio.objetos_de_valor.conversa import AcaoIntervencao, AutorMensagem


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
    autor: AutorMensagem = Field(
        default=None,
        description="Autor da mensagem: usuário/lead ou humano da empresa.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message_id": "msg-123",
                    "tenant_id": "sol-nascente",
                    "telefone": "5581988887777",
                    "texto": "Olá, tenho interesse",
                    "timestamp": "2026-01-01T10:00:00",
                }
            ]
        }
    )


class IntervencaoSerializador(BaseModel):
    tenant_id: str = Field(
        description="Identificador do tenant.",
        examples=["empresa-1"],
    )
    telefone: str = Field(
        description="Telefone do lead.",
        examples=["11999999999"],
    )
    acao: AcaoIntervencao = Field(
        description="Ação de intervenção humana.",
        examples=[AcaoIntervencao.ASSUMIR],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tenant_id": "empresa-1",
                    "telefone": "11999999999",
                    "acao": "assumir",
                }
            ]
        }
    )


class IntervencaoResposta(BaseModel):
    tenant_id: str = Field(description="Identificador do tenant.")
    telefone: str = Field(description="Telefone do lead.")
    teve_intervencao_humana: bool = Field(
        description="Indica se houve intervenção humana na conversa."
    )


class MensagemResposta(BaseModel):
    id: UUID = Field(description="Identificador da mensagem.")
    identificador_da_mensagem: str = Field(
        description="Identificador externo da mensagem."
    )
    texto: str = Field(description="Conteúdo da mensagem.")
    foi_gerada_pela_ia: bool = Field(
        description="Indica se a mensagem foi gerada pela IA."
    )
    foi_respondida_pelo_usuario: bool = Field(
        description="Indica se a mensagem foi respondida pelo usuário/lead."
    )
    foi_intervencao_humana: bool = Field(
        description="Indica se a mensagem foi uma intervenção humana da empresa."
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
        description=(
            "Mensagens retornadas; contém a última mensagem gerada pela IA ou a "
            "última intervenção humana, conforme o estado da conversa."
        )
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
                            "foi_gerada_pela_ia": False,
                            "foi_respondida_pelo_usuario": True,
                            "foi_intervencao_humana": False,
                            "criado_em": "2026-01-01T10:00:00",
                        }
                    ],
                }
            ]
        },
    )
