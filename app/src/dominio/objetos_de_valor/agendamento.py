from enum import StrEnum


class StatusDoAgendamento(StrEnum):
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"


class Telefone(str): ...
