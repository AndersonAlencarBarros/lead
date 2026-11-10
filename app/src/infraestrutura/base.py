from sqlalchemy.orm import DeclarativeBase, registry


class Base(DeclarativeBase):
    pass


mapper_registry = registry(metadata=Base.metadata)
