from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dominio.objetos_de_valor.empresa import StatusEmpresa, TomDaIA


class IntervaloSerializador(BaseModel):
    horario_inicio: datetime
    horario_fim: datetime

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.horario_inicio >= self.horario_fim:
            raise ValueError("horario_inicio deve ser anterior a horario_fim")
        return self


class ConfiguracaoIASerializador(BaseModel):
    tom: TomDaIA
    pode_dizer_que_e_ia: bool
    nome_assistente: str
    horario_atendimento_ia: IntervaloSerializador


EXEMPLO_EMPRESA_SOL_NASCENTE = {
    "tenant_id": "sol-nascente",
    "nome": "Sol Nascente Energia Solar",
    "status": "ativa",
    "telefone_notificacao": "5581988887777",
    "janela_de_resposta": 8,
    "configuracao_ia": {
        "tom": "informal",
        "pode_dizer_que_e_ia": True,
        "nome_assistente": "Luz",
        "horario_atendimento_ia": {
            "horario_inicio": "2026-01-01T00:00:00",
            "horario_fim": "2026-01-01T23:59:59",
        },
    },
    "regras_gerais": [
        "Nunca prometer valor exato de economia; dizer que depende da visita técnica.",
        "Nunca informar preço final; dizer que o consultor apresenta o orçamento.",
        "Não pedir nem repetir senhas ou dados bancários.",
        (
            "Se o lead disser que já é cliente, marcar 'cliente-antigo' "
            "e transferir para humano."
        ),
    ],
    "cidades_atendidas": [
        "Recife",
        "Olinda",
        "Jaboatão dos Guararapes",
        "Caruaru",
    ],
    "estagios": [
        "Novo",
        "Qualificacao",
        "Qualificado",
        "Desqualificado",
        "Agendado",
        "Humano",
    ],
}


class EmpresaCriacaoSerializador(BaseModel):
    tenant_id: str = Field(min_length=1)
    nome: str = Field(min_length=1)
    status: StatusEmpresa = StatusEmpresa.ATIVA
    telefone_notificacao: str = Field(min_length=1)
    janela_de_resposta: float = Field(default=10, gt=0)
    configuracao_ia: ConfiguracaoIASerializador
    regras_gerais: list[str] = Field(default_factory=list)
    cidades_atendidas: list[str] = Field(default_factory=list)
    estagios: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={"examples": [EXEMPLO_EMPRESA_SOL_NASCENTE]}
    )


class EmpresaResposta(BaseModel):
    id: UUID
    tenant_id: str
    nome: str
    status: StatusEmpresa
    telefone_notificacao: str
    criado_em: datetime
    janela_de_resposta: float
    configuracao_ia: ConfiguracaoIASerializador
    regras_gerais: list[str]
    cidades_atendidas: list[str]
    estagios: list[str]

    model_config = ConfigDict(from_attributes=True)
