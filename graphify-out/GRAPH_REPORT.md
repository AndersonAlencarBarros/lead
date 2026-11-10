# Graph Report - motor-ia  (2026-11-09)

## Corpus Check
- Corpus is ~4,675 words - fits in a single context window. You may not need a graph.

## Summary
- 321 nodes · 478 edges · 34 communities (12 shown, 22 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 49 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Fluxo de conversa (API, repositório, serialização)
- Sessão, fixtures e bootstrap
- Pipeline CD GitHub Actions
- Domínio empresa e agendamento
- Agregado conversa e mensagens
- Migrations Alembic e banco
- Teste de carga Artillery
- Pipeline CI GitHub Actions
- Configuração e engine do banco
- Instruções e skills do projeto
- Domínio lead
- Exceções HTTP
- Metadados do app (pyproject)

## God Nodes (most connected - your core abstractions)
1. `UnidadeDeTrabalho` - 17 edges
2. `Conversa` - 16 edges
3. `Session` - 16 edges
4. `Empresa` - 11 edges
5. `Dominio` - 9 edges
6. `ConversaLeituraRepositorio` - 9 edges
7. `steps` - 8 edges
8. `Settings` - 8 edges
9. `_criar_conversa()` - 8 edges
10. `ConversaDominioRepositorio` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Fluxo de trabalho em sete passos` --semantically_similar_to--> `Implementação em seis passos`  [INFERRED] [semantically similar]
  AGENTS.md → SKILL/economia-tokens.md
- `Economia de tokens (diretrizes do projeto)` --semantically_similar_to--> `Regras de economia de tokens`  [INFERRED] [semantically similar]
  AGENTS.md → SKILL/economia-tokens.md
- `Motor de IA para leads` --conceptually_related_to--> `App FastAPI (cadastro de usuários e testes de CI/CD)`  [INFERRED]
  README.md → app/README.md
- `receber_mensagem_api()` --references--> `post`  [EXTRACTED]
  app/src/api/conversa.py → asciiart-load-test.yml
- `Conexão e engine do banco (config.py + session.py)` --references--> `Settings`  [EXTRACTED]
  app/README.md → app/src/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Economia de tokens (projeto e skill)** — agents_economia_de_tokens, skill_economia_tokens_regras, skill_economia_tokens_limites [INFERRED 0.85]
- **Camada de persistência documentada** — app_readme_banco_e_engine, app_readme_pool_de_conexoes, app_readme_normalizacao_de_url, app_readme_migrations_alembic [INFERRED 0.85]
- **Pipeline CI/CD, testes de carga e deploy** — app_readme_teste_de_load_artillery, app_readme_cloud_run, github_workflows_cd_pipeline, github_workflows_ci_pipeline [INFERRED 0.75]

## Communities (34 total, 22 thin omitted)

### Community 0 - "Fluxo de conversa (API, repositório, serialização)"
Cohesion: 0.07
Nodes (12): buscar_conversa_api(), receber_mensagem_api(), Dominio, ParRepositorio, UnidadeDeTrabalho, ConversaDominioRepositorio, ConversaLeituraRepositorio, receber_mensagem() (+4 more)

### Community 1 - "Sessão, fixtures e bootstrap"
Cohesion: 0.08
Nodes (16): Stack do projeto (Python, FastAPI, PostgreSQL, Docker, ETL), Verificação da stack real nos arquivos, App FastAPI (cadastro de usuários e testes de CI/CD), Conexão e engine do banco (config.py + session.py), Deploy no Cloud Run e dimensionamento do pool, Endpoints documentados (/users, /health), Pool de conexões (DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE, DB_PRE_PING), Stack do app (FastAPI, SQLAlchemy async, Alembic, pytest, testcontainers) (+8 more)

### Community 2 - "Pipeline CD GitHub Actions"
Cohesion: 0.07
Nodes (33): name, needs, runs-on, steps, run, env, D_PASS, D_USER (+25 more)

### Community 3 - "Domínio empresa e agendamento"
Cohesion: 0.11
Nodes (13): Agendamento, Auditoria, Empresa, StatusDoAgendamento, Cidade, ConfiguracaoIA, Estagio, HorarioInvalido (+5 more)

### Community 4 - "Agregado conversa e mensagens"
Cohesion: 0.13
Nodes (8): Conversa, Mensagem, Telefone, Base, _criar_conversa(), _get(), test_get_conversa_inexistente_retorna_404(), test_get_conversa_retorna_mensagens_associadas()

### Community 5 - "Migrations Alembic e banco"
Cohesion: 0.09
Nodes (7): Migrations Alembic fora da raiz, Revision 0001_baseline vazia, do_run_migrations(), run_async_migrations(), run_migrations_offline(), run_migrations_online(), upgrade()

### Community 6 - "Teste de carga Artillery"
Cohesion: 0.08
Nodes (23): Teste de load com Artillery, expression, config, phases, plugins, target, conditions, thresholds (+15 more)

### Community 7 - "Pipeline CI GitHub Actions"
Cohesion: 0.09
Nodes (21): run, jobs, test, name, on, pull_request, push, branches (+13 more)

### Community 8 - "Configuração e engine do banco"
Cohesion: 0.12
Nodes (6): Normalização de DATABASE_URL (postgres:// para postgresql+psycopg://), get_settings(), Settings, test_pool_settings_are_overridable_by_environment(), test_settings_keep_the_query_string(), test_settings_use_the_async_postgres_dialect()

### Community 9 - "Instruções e skills do projeto"
Cohesion: 0.27
Nodes (3): docs/ai/ — documentação de arquitetura, testes e banco, Instruções do projeto para IA, Skill economia-tokens

### Community 10 - "Domínio lead"
Cohesion: 0.44
Nodes (5): Lead, Cidade, EstagioDoLead, Nome, Telefone

### Community 11 - "Exceções HTTP"
Cohesion: 0.28
Nodes (3): ConversaNaoEncontrada, EmailJaCadastrado, RespostaDoUsuario

## Knowledge Gaps
- **5 isolated node(s):** `app`, `Motor de IA para leads`, `docs/ai/ — documentação de arquitetura, testes e banco`, `Normalização de DATABASE_URL (postgres:// para postgresql+psycopg://)`, `Deploy no Cloud Run e dimensionamento do pool`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 140 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `App FastAPI (cadastro de usuários e testes de CI/CD)` connect `Sessão, fixtures e bootstrap` to `Migrations Alembic e banco`, `Teste de carga Artillery`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `UnidadeDeTrabalho` (e.g. with `buscar_conversa_api()` and `receber_mensagem_api()`) actually correct?**
  _`UnidadeDeTrabalho` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `app`, `Motor de IA para leads`, `docs/ai/ — documentação de arquitetura, testes e banco` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Fluxo de conversa (API, repositório, serialização)` be split into smaller, more focused modules?**
  _Cohesion score 0.07482993197278912 - nodes in this community are weakly interconnected._
- **Why does `Session` connect `Sessão, fixtures e bootstrap` to `Fluxo de conversa (API, repositório, serialização)`, `Configuração e engine do banco`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Conversa` (e.g. with `Mensagem` and `Telefone`) actually correct?**
  _`Conversa` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `Sessão, fixtures e bootstrap` be split into smaller, more focused modules?**
  _Cohesion score 0.08199643493761141 - nodes in this community are weakly interconnected._