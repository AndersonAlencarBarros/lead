from uuid import UUID

from dominio.agregados import Agregado


class Auditoria(Agregado):
    id: UUID
    acao: str
    empresa_id: UUID
    endereco_ip: str
    telefone: str
