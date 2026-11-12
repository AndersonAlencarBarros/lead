from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dominio.objetos_de_valor.empresa import StatusEmpresa, TomDaIA
from dominio.objetos_de_valor.ferramenta import NomeFerramenta
from dominio.objetos_de_valor.playbook import TipoCampo


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


class CampoDaFichaSerializador(BaseModel):
    nome: str = Field(min_length=1)
    descricao: str = Field(min_length=1)
    tipo: TipoCampo
    opcoes: list[str] = Field(default_factory=list)
    obrigatorio: bool = False

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validar_opcoes(self):
        if self.tipo is TipoCampo.OPCAO and not self.opcoes:
            raise ValueError("campo opcao precisa de opcoes")
        if self.tipo is not TipoCampo.OPCAO and self.opcoes:
            raise ValueError("opcoes so valem para campo opcao")
        return self


class PlaybookSerializador(BaseModel):
    nome: str = Field(min_length=1)
    versao: int = Field(default=1, ge=1)
    objetivo: str = Field(min_length=1)
    perguntas: list[str] = Field(min_length=1)
    campos: list[CampoDaFichaSerializador] = Field(min_length=1)
    criterios_de_qualificacao: list[str] = Field(default_factory=list)
    regras: list[str] = Field(default_factory=list)
    ferramentas: list[NomeFerramenta] = Field(min_length=1)

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validar_playbook(self):
        nomes = [campo.nome for campo in self.campos]
        if len(nomes) != len(set(nomes)):
            raise ValueError("campos duplicados na ficha")
        if NomeFerramenta.ATUALIZAR_FICHA in self.ferramentas and not self.campos:
            raise ValueError("atualizar_ficha exige campos")
        return self


EXEMPLO_PLAYBOOK_SOL_NASCENTE = {
    "nome": "energia-solar-residencial",
    "versao": 1,
    "objetivo": "Qualificar lead e agendar visita técnica.",
    "perguntas": [
        "Qual o nome e a cidade?",
        "O imóvel é próprio ou alugado?",
        "É casa ou apartamento?",
        "Qual o valor médio da conta de luz?",
        "Tem interesse em financiar ou pagar à vista?",
    ],
    "campos": [
        {
            "nome": "nome",
            "descricao": "Nome do lead",
            "tipo": "texto",
            "obrigatorio": True,
        },
        {
            "nome": "cidade",
            "descricao": "Cidade do imóvel",
            "tipo": "texto",
            "obrigatorio": True,
        },
        {
            "nome": "imovel",
            "descricao": "Imóvel próprio ou alugado",
            "tipo": "opcao",
            "opcoes": ["proprio", "alugado"],
            "obrigatorio": True,
        },
        {
            "nome": "tipo_imovel",
            "descricao": "Casa ou apartamento",
            "tipo": "opcao",
            "opcoes": ["casa", "apartamento"],
            "obrigatorio": True,
        },
        {
            "nome": "valor_conta",
            "descricao": "Conta de luz mensal",
            "tipo": "numero",
            "obrigatorio": True,
        },
        {
            "nome": "financiamento",
            "descricao": "Forma de pagamento",
            "tipo": "opcao",
            "opcoes": ["financiado", "a_vista"],
            "obrigatorio": False,
        },
    ],
    "criterios_de_qualificacao": [
        "Imóvel próprio, casa, conta acima de R$ 250 e cidade atendida."
    ],
    "regras": [
        "Nunca prometer economia exata.",
        "Nunca informar preço final.",
    ],
    "ferramentas": [
        "adicionar_tag",
        "mover_estagio",
        "atualizar_ficha",
        "notificar_equipe",
        "transferir_humano",
        "consultar_agenda",
        "marcar_agenda",
    ],
}


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
    "playbook": EXEMPLO_PLAYBOOK_SOL_NASCENTE,
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
    playbook: PlaybookSerializador

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
    playbook: PlaybookSerializador

    model_config = ConfigDict(from_attributes=True)
