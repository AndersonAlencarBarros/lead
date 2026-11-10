# App

API de atendimento por conversas: recebe mensagens por webhook e expõe
consultas de conversas e mensagens.

## Stacks

- Python 3.13+
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) 2.x assíncrono + [psycopg](https://www.psycopg.org/psycopg3/) 3 (Postgres)
- [Alembic](https://alembic.sqlalchemy.org/) para migrations
- [pytest](https://docs.pytest.org/) + TestClient (httpx) + [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) + [testcontainers](https://testcontainers-python.readthedocs.io/)

## Estrutura

```text
app/
├── src/                              # código da aplicação (em sys.path)
│   ├── main.py                       # bootstrap do FastAPI (uvicorn main:app)
│   ├── config.py                     # Settings (pydantic-settings)
│   ├── api/                          # routers FastAPI
│   │   ├── __init__.py               # api_router (agrega os routers)
│   │   └── conversa.py               # webhook e consulta de conversas
│   ├── dominio/                      # regras de negócio
│   ├── servicos/                     # executores, serializadores, visualizadores
│   ├── repositorio/                  # persistência
│   └── infraestrutura/               # SQLAlchemy async + migrations
│       ├── base.py                   # Base declarativa
│       ├── session.py                # engine e sessions
│       └── alembic/                  # alembic.ini, env.py, script.py.mako, versions/
└── testes/
    ├── unitario/                     # testes sem banco
    │   └── config/
    └── integracao/                   # pytest (+ testcontainers)
        ├── api/
        │   ├── conversa/
        │   └── empresa/
        ├── infraestrutura/
        │   └── banco/
        └── servicos/
            ├── agendamento/
            └── lead/
```

`main` e `config` são módulos de topo (importados por nome); `api`, `dominio`,
`servicos`, `repositorio` e `infraestrutura` são pacotes de `src/`.

## Como rodar

```bash
poetry install
cp .env.example .env    # SQLite local por padrão; ajuste para Postgres se necessário
poetry run alembic -c src/infraestrutura/alembic/alembic.ini upgrade head
poetry run uvicorn main:app --reload
```

Testes:

```bash
poetry run pytest                    # suíte completa
poetry run pytest testes/unitario    # sem Docker
poetry run pytest testes/integracao  # com Docker
```

Os testes de banco sobem um Postgres 16 real em container
([testcontainers](https://testcontainers-python.readthedocs.io/)), então é preciso
Docker disponível — não é preciso ter um Postgres instalado na máquina, nem
configurar `DATABASE_URL`.

## Migrations

```bash
poetry run alembic -c src/infraestrutura/alembic/alembic.ini upgrade head                       # aplica
poetry run alembic -c src/infraestrutura/alembic/alembic.ini downgrade -1                       # desfaz
poetry run alembic -c src/infraestrutura/alembic/alembic.ini revision --autogenerate -m "msg"   # cria revision
```

O `alembic.ini` fica dentro de `src/infraestrutura/alembic/`, junto do `env.py`
e das migrations. Como ele não está na raiz, o `-c` é obrigatório — o Alembic
procura `alembic.ini` (e também `pyproject.toml`) no diretório atual.
Alternativa, que dispensa a flag:

```bash
export ALEMBIC_CONFIG=src/infraestrutura/alembic/alembic.ini
poetry run alembic upgrade head
```

O arquivo lê a URL de `Settings`, ou seja, as mesmas variáveis de ambiente da
aplicação, e adiciona `src/` ao `sys.path` via `prepend_sys_path`. O `env.py`
usa `infraestrutura.base.Base.metadata` como `target_metadata`.

A revision `0001_baseline` é intencionalmente vazia; as tabelas entram na
revision seguinte.

## Endpoints

| Método | Rota | Descrição |
| ------ | ---- | --------- |
| POST | `/empresas` | Cria empresa; `201` ou `409` se o tenant já existir |
| POST | `/webhook/mensagem` | Recebe mensagem: `201` para nova, `204` para duplicada |
| GET | `/conversas/{tenant_id}/{telefone}` | Retorna conversa e mensagens; `404` se não existir |

A documentação interativa fica em `/docs` e `/redoc`, e o schema em
`/openapi.json`.
