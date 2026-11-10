from dataclasses import dataclass


@dataclass
class Auditoria:
    id: str
    acao: str
    empresa: str
    endereco_ip: str
    telefone: str



