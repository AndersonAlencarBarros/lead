from datetime import datetime
from enum import StrEnum
from uuid import UUID

from dominio.agregados import Agregado


class StatusTurno(StrEnum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    FALHOU = "falhou"


class TurnoIA(Agregado):
    id: UUID | None
    conversa_id: UUID
    tenant_id: str
    mensagem_origem_id: str
    status: StatusTurno
    modelo: str | None
    tokens_entrada: int
    tokens_saida: int
    custo_estimado: float
    latencia_ms: int
    erro: str | None
    criado_em: datetime

    def __init__(
        self,
        conversa_id: UUID,
        tenant_id: str,
        mensagem_origem_id: str,
        status: StatusTurno = StatusTurno.EM_ANDAMENTO,
        modelo: str | None = None,
        tokens_entrada: int = 0,
        tokens_saida: int = 0,
        custo_estimado: float = 0.0,
        latencia_ms: int = 0,
        erro: str | None = None,
        id: UUID | None = None,
        criado_em: datetime | None = None,
    ):
        self.id = id
        self.conversa_id = conversa_id
        self.tenant_id = tenant_id
        self.mensagem_origem_id = mensagem_origem_id
        self.status = StatusTurno(status)
        self.modelo = modelo
        self.tokens_entrada = tokens_entrada
        self.tokens_saida = tokens_saida
        self.custo_estimado = custo_estimado
        self.latencia_ms = latencia_ms
        self.erro = erro
        self.criado_em = criado_em or datetime.now()

    def concluir(
        self,
        modelo: str,
        tokens_entrada: int,
        tokens_saida: int,
        custo_estimado: float,
        latencia_ms: int,
    ) -> None:
        self.status = StatusTurno.CONCLUIDO
        self.modelo = modelo
        self.tokens_entrada = tokens_entrada
        self.tokens_saida = tokens_saida
        self.custo_estimado = custo_estimado
        self.latencia_ms = latencia_ms
        self.erro = None

    def falhar(self, erro: str) -> None:
        self.status = StatusTurno.FALHOU
        self.erro = erro
