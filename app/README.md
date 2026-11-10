# App

Pequeno projeto de cadastro de usuários (nome e email) com FastAPI e testes
unitários, feito para validar pipelines de CI/CD.

## Stacks

- Python 3.11+
- [FastAPI](https://fastapi.tiangolo.com/) com armazenamento em memória
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
│   │   ├── usuarios.py               # /users
│   │   └── saude.py                  # /health
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
        │   ├── saude/
        │   └── usuario/
        ├── infraestrutura/
        │   ├── banco/
        │   └── unidade_de_trabalho/
        └── servicos/
            └── usuario/
```

`main` e `config` são módulos de topo (importados por nome); `api`, `dominio`,
`servicos`, `repositorio` e `infraestrutura` são pacotes de `src/`.

## Como rodar

```bash
poetry install
cp .env.example .env    # e ajuste DATABASE_URL (por padrão, SQLite local)
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

## Banco de dados

A conexão é criada por [`config.py`](src/config.py) e o engine por
[`infraestrutura/session.py`](src/infraestrutura/session.py).

| Variável           | Default | Descrição                                        |
| ------------------ | ------- | ------------------------------------------------ |
| `DATABASE_URL`     | —       | Obrigatória. URL do banco                       |
| `DB_POOL_SIZE`     | `5`     | Conexões mantidas abertas por instância         |
| `DB_MAX_OVERFLOW`  | `10`    | Conexões extras sob demanda                      |
| `DB_POOL_TIMEOUT`  | `30`    | Segundos de espera por uma conexão do pool       |
| `DB_POOL_RECYCLE`  | `1800`  | Idade máxima de uma conexão do pool, em segundos |
| `DB_POOL_PRE_PING` | `true`  | Valida a conexão antes de emprestá-la             |
| `DB_ECHO`          | `false` | Loga o SQL executado                             |

Detalhes:

- As URL `postgres://` e `postgresql://` são normalizadas para
  `postgresql+psycopg://`, que é o dialeto assíncrono. Provedores gerenciados
  (Neon, Supabase, RDS) costumam entregar `postgres://` com
  `?sslmode=require` — a query string é preservada.
- Localmente o default é SQLite (`sqlite+aiosqlite:///./db.sqlite3`, arquivo
  `app/db.sqlite3`). O esquema `sqlite://` também é normalizado para
  `sqlite+aiosqlite://`; o arquivo usa pool `AsyncAdaptedQueuePool`, que aceita
  as variáveis de pool abaixo.
- O engine é criado de forma preguiçosa no primeiro uso e devolvido no
  shutdown (lifespan do FastAPI).
- Em `.env` (dev) e em variáveis de ambiente (deploy) a leitura é a mesma; a
  variável de ambiente tem prioridade sobre o arquivo.
- O `.env` está no `.gitignore` e no `.dockerignore` — ele nunca entra na imagem.

### Pool e Cloud Run

O total de conexões é `(DB_POOL_SIZE + DB_MAX_OVERFLOW) * número de instâncias`.
Cloud Run pode abrir várias instâncias, então em provedores com limite baixo de
conexões use `DB_POOL_SIZE=2` e `DB_MAX_OVERFLOW=0`.

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

A revision `0001_baseline` é intencionalmente vazia: os modelos entram na
próxima etapa, e é a partir dela que o `--autogenerate` passa a gerar DDL.

## Endpoints

| Método | Rota            | Descrição                    |
| ------ | --------------- | ---------------------------- |
| POST   | `/users`        | Cadastra um usuário (201)    |
| GET    | `/users`        | Lista usuários cadastrados   |
| GET    | `/users/{id}`   | Busca usuário por id (404 se não existir) |
| GET    | `/health`       | Verifica a API e o banco (`SELECT 1`) |

Regras de validação:

- `name` não pode ser vazio
- `email` deve ter formato válido
- email duplicado retorna `409`

`/health` retorna `500` quando o banco está inacessível. Em deploy, a
`DATABASE_URL` precisa ser injetada no Cloud Run (secret) para que ele passe.

## Teste de load (Artillery)

O arquivo [`asciiart-load-test.yml`](../asciiart-load-test.yml) na raiz envia
100 requisições `POST /users` (5 req/s por 20s) contra o Cloud Run.

Requisitos: Node.js 18+ (o Artillery roda via `npx`, sem instalação global).

```bash
# a partir da raiz do repositório
npx artillery run asciiart-load-test.yml
```

O que é validado no fim do teste:

- `http.codes.201 == 100` — todas as 100 requisições devem criar o usuário
- `http.response_time.p95 < 3000` e `p99 < 5000` — limites de latência
- Exit code 0 = passou; 1 = algum check falhou (seção "Checks" do relatório)

Cada requisição usa um e-mail único (`loadtest-{{$uuid}}@example.com`) para
evitar `409` de e-mail duplicado.