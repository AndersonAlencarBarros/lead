from enum import StrEnum


class EstagioDoLead(StrEnum):
    QUALIFICADO = 'qualificado'
    DESQUALIFICADO = 'desqualificado'
    AGENDADO = 'agendado'

class Telefone(str):
    ...

class Nome(str):
    ...

class Cidade(str):
    ...
