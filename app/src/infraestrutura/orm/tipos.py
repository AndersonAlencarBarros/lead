from enum import StrEnum

from sqlalchemy import String, TypeDecorator


class EnumString(TypeDecorator):
    """Persiste StrEnum como string e devolve o membro do enum ao carregar."""

    impl = String
    cache_ok = True

    def __init__(self, enum_class: type[StrEnum], length: int = 20):
        self.enum_class = enum_class
        super().__init__(length=length)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return self.enum_class(value).value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum_class(value)
