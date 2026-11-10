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
