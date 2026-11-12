# App

API de atendimento por conversas: recebe mensagens por webhook e expõe
consultas de conversas e mensagens.

## Stacks

- Python 3.13+
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) 2.x assíncrono + [psycopg](https://www.psycopg.org/psycopg3/) 3 (Postgres)
- [Alembic](https://alembic.sqlalchemy.org/) para migrations
- [LiteLLM](https://docs.litellm.ai/) + OpenRouter para respostas da IA
- [Celery](https://docs.celeryq.dev/) + Redis para geração assíncrona
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
│   │   └── regras_de_negocio/
│   │       └── servico_ia/           # contexto, provider, serviço e task
│   ├── servicos/                     # executores, serializadores, visualizadores
│   ├── repositorio/                  # persistência
│   └── infraestrutura/               # SQLAlchemy async + migrations
│       ├── base.py                   # Base declarativa
│       ├── session.py                # engine e sessions
│       ├── celery_app.py             # configuração do Celery
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
# edite .env e defina OPEN_ROUTER_KEY
poetry run uvicorn main:app --reload
```

Em outro terminal, suba o Redis e o worker Celery (a partir da raiz):

```bash
make redis
make celery
```

O webhook persiste a mensagem e enfileira a resposta. O worker gera e grava a
resposta da IA; a consulta `GET /conversas/...` retorna a última mensagem
gerada pela IA.
Ajuste `LLM_MODEL`, `OPEN_ROUTER_KEY` e `CELERY_BROKER_URL` no
`.env` conforme o ambiente.

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

### Testes com LLM real

Os testes em `testes/integracao/ia/` chamam a OpenRouter, usando o modelo
`liquid/lfm-3-1.7b:free`.

```bash
make test-ia
# ou
poetry run pytest testes/integracao/ia -v
```

Se `OPEN_ROUTER_KEY` estiver ausente, os testes são ignorados.

### Dados de exemplo

Cria ou atualiza os tenants de exemplo `sol-nascente` e `confeitaria-encanto`:

```bash
poetry run python script/persistir_exemplos_de_tenant.py
```

O script é idempotente: cria o tenant quando ausente e atualiza o playbook quando ele já existe.

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

## Respostas da IA

O webhook grava a mensagem e enfileira `responder_conversa_task`. O worker só
responde quando a empresa do tenant existe, a conversa permite resposta
automática e a última mensagem é a recém-recebida. Falhas da LLM são
reprocessadas até 3 vezes. A resposta é gravada em `mensagens` com
`foi_gerada_pela_ia=true` e um identificador determinístico, evitando
duplicatas.

A IA só responde quando a empresa está `ativa` e o horário atual está dentro de
`horario_atendimento_ia`. Fora do horário, a task grava uma mensagem automática
informando o horário configurado, sem chamar a LLM. Empresas `inativa` ou
`suspensa` não respondem.

A resposta é agendada com `countdown` igual a `janela_de_resposta`. Quando a task
roda, só a última mensagem do lead responde, considerando todas as mensagens
pendentes desde a última resposta da IA mais o histórico de intervenção humana.

As mensagens usam três flags de origem:

- `foi_gerada_pela_ia`: mensagem gerada pela IA.
- `foi_respondida_pelo_usuario`: mensagem enviada pelo lead/usuário.
- `foi_intervencao_humana`: mensagem enviada por humano da empresa.

## Intervenção humana

Mensagens do webhook com `"autor": "humano"` são gravadas como intervenção
humana e assumem a conversa automaticamente. Sem `autor`, a mensagem é tratada
como do lead/usuário.

`POST /intervencao` com `acao=assumir` marca a conversa como assumida e a IA
para de responder. `acao=religar` devolve o atendimento para a IA e enfileira
uma resposta para a última mensagem do lead ainda sem resposta. A IA recebe no
contexto a janela atual de mensagens mais todo o histórico de intervenção
humana. Durante a intervenção, as mensagens continuam sendo gravadas, mas não
são enfileiradas para a IA.

`GET /conversas/{tenant_id}/{telefone}` retorna a última mensagem da intervenção
humana enquanto a conversa estiver assumida. Sem intervenção, retorna a última
mensagem gerada pela IA.

## Endpoints

| Método | Rota | Descrição |
| ------ | ---- | --------- |
| POST | `/empresas` | Cria empresa; `201` ou `409` se o tenant já existir |
| POST | `/webhook/mensagem` | Recebe mensagem: `201` para nova, `204` para duplicada; `503` se a fila estiver indisponível |
| POST | `/intervencao` | `assumir` ativa a intervenção humana; `religar` devolve o atendimento para a IA |
| GET | `/conversas/{tenant_id}/{telefone}` | Retorna a última mensagem da IA ou da intervenção humana; `404` se não existir |

A documentação interativa fica em `/docs` e `/redoc`, e o schema em
`/openapi.json`.
