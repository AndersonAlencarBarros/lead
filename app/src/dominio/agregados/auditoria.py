from datetime import datetime
from typing import Any
from uuid import UUID

from dominio.agregados import Agregado


class Auditoria(Agregado):
    id: UUID | None
    turno_id: UUID
    conversa_id: UUID
    lead_id: UUID | None
    ferramenta: str
    argumentos: dict[str, Any]
    resultado: dict[str, Any] | None
    sucesso: bool
    erro: str | None
    hash_argumentos: str
    criado_em: datetime

    def __init__(
        self,
        turno_id: UUID,
        conversa_id: UUID,
        lead_id: UUID | None,
        ferramenta: str,
        argumentos: dict[str, Any],
        hash_argumentos: str,
        resultado: dict[str, Any] | None = None,
        sucesso: bool = True,
        erro: str | None = None,
        id: UUID | None = None,
        criado_em: datetime | None = None,
    ):
        self.id = id
        self.turno_id = turno_id
        self.conversa_id = conversa_id
        self.lead_id = lead_id
        self.ferramenta = ferramenta
        self.argumentos = argumentos
        self.resultado = resultado
        self.sucesso = sucesso
        self.erro = erro
        self.hash_argumentos = hash_argumentos
        self.criado_em = criado_em or datetime.now()
