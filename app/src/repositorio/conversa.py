from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dominio.agregados.conversa import Conversa
from dominio.agregados.empresa import Empresa
from dominio.objetos_de_valor.conversa import Mensagem
from infraestrutura.orm.orm_conversa import conversas_tabela  # noqa: F401
from infraestrutura.orm.orm_empresa import empresas_tabela  # noqa: F401
from repositorio import Repositorio


class ConversaMixin:
    """Consulta compartilhada entre os repositórios de Conversa."""

    session: AsyncSession

    async def buscar_por_empresa_e_telefone(
        self, tenant_id: str, telefone: str
    ) -> Conversa | None:
        """Busca conversa por empresa e telefone, carregando as mensagens associadas."""
        stmt = (
            select(Conversa)
            .where((Conversa.tenant_id == tenant_id) & (Conversa.telefone == telefone))
            .options(selectinload(Conversa.mensagens))
        )
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()


class ConversaDominioRepositorio(ConversaMixin, Repositorio):
    """Repositório de domínio (escrita e mutação do agregado Conversa)."""

    async def salvar(self, conversa: Conversa) -> Conversa:
        """Persiste ou atualiza o agregado Conversa."""
        self.session.add(conversa)
        await self.session.flush()
        await self.session.refresh(conversa)
        return conversa

    async def buscar_empresa_por_tenant_id(self, tenant_id: str) -> Empresa | None:
        """Busca a empresa associada ao tenant informado."""
        stmt = select(Empresa).where(Empresa.tenant_id == tenant_id)
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one_or_none()


class ConversaLeituraRepositorio(ConversaMixin, Repositorio):
    """Repositório de leitura (consultas e projeções de Conversa)."""

    async def mensagem_existe(self, identificador: str) -> bool:
        """Verifica se uma mensagem já foi persistida pelo identificador externo."""
        stmt = select(
            exists().where(Mensagem.identificador_da_mensagem == identificador)
        )
        resultado = await self.session.execute(stmt)
        return resultado.scalar_one()
