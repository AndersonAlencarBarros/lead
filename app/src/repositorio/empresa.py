from sqlalchemy import select

from dominio.agregados.empresa import Empresa
from infraestrutura.orm.orm_empresa import empresas_tabela  # noqa: F401
from repositorio import Repositorio


class EmpresaDominioRepositorio(Repositorio):
    """Repositório de domínio (escrita e mutação do agregado Empresa)."""

    async def salvar(self, empresa: Empresa) -> Empresa:
        """Persiste ou atualiza o agregado Empresa."""
        self.session.add(empresa)
        await self.session.flush()
        await self.session.refresh(empresa)
        return empresa


class EmpresaLeituraRepositorio(Repositorio):
    """Repositório de leitura (consultas de Empresa)."""

    async def buscar_por_tenant_id(self, tenant_id: str) -> Empresa | None:
        stmt = select(Empresa).where(Empresa.tenant_id == tenant_id)
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()

    async def buscar_por_id(self, empresa_id) -> Empresa | None:
        stmt = select(Empresa).where(Empresa.id == empresa_id)
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()
