"""Cria ou atualiza os tenants de exemplo.

Pré-requisito:
    cd app
    poetry run alembic -c src/infraestrutura/alembic/alembic.ini upgrade head

Uso:
    cd app
    poetry run python script/persistir_exemplos_de_tenant.py
"""

import asyncio
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
os.chdir(APP_DIR)
sys.path.insert(0, str(APP_DIR / "src"))
sys.path.insert(0, str(APP_DIR))

from infraestrutura.session import Session
from infraestrutura.unidade_de_trabalho import Dominio, UnidadeDeTrabalho
from servicos.executores.empresa import criar_empresa, montar_playbook
from servicos.serializadores.empresa import (
    EXEMPLO_EMPRESA_CONFEITARIA,
    EXEMPLO_EMPRESA_SOL_NASCENTE,
    EmpresaCriacaoSerializador,
)

EXEMPLOS = (
    EXEMPLO_EMPRESA_SOL_NASCENTE,
    EXEMPLO_EMPRESA_CONFEITARIA,
)


async def reseed_tenant(exemplo: dict) -> None:
    payload = EmpresaCriacaoSerializador(**exemplo)

    async with UnidadeDeTrabalho(Dominio.EMPRESA) as uow:
        existente = await uow.leitura.buscar_por_tenant_id(payload.tenant_id)
        if existente is not None:
            existente.atualizar_playbook(montar_playbook(payload.playbook))
            await uow.dominio.salvar(existente)
            await uow.commit()
            print(f"tenant atualizado: {existente.tenant_id} ({existente.id})")
            return

        empresa = await criar_empresa(payload, uow)
        await uow.commit()
        print(f"tenant criado: {empresa.tenant_id} ({empresa.id})")


async def reseed() -> None:
    try:
        for exemplo in EXEMPLOS:
            await reseed_tenant(exemplo)
    finally:
        await Session.dispose()


if __name__ == "__main__":
    asyncio.run(reseed())
