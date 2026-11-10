# Graph Report - ETL-Python  (2026-10-29)

## Corpus Check
- Corpus is ~5,488 words - fits in a single context window. You may not need a graph.

## Summary
- 322 nodes · 491 edges · 33 communities (9 shown, 24 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 68 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Configuration and Deployment
- User API Endpoints
- User Domain and Repositories
- CD Pipeline Workflow
- Health and Session Management
- Alembic Migration Environment
- Artillery Load Testing
- CI Pipeline Workflow
- Settings and Unit Tests
- Session and Unit of Work
- Application Package

## God Nodes (most connected - your core abstractions)
1. `Usuario` - 24 edges
2. `UnidadeDeTrabalho` - 24 edges
3. `Session` - 17 edges
4. `Dominio` - 14 edges
5. `salvar_usuario()` - 13 edges
6. `UsuarioLeituraRepositorio` - 12 edges
7. `CriarUsuario` - 9 edges
8. `steps` - 8 edges
9. `UsuarioRepositorio` - 8 edges
10. `Settings` - 7 edges

## Surprising Connections (you probably didn't know these)
- `SQLAlchemy Async` --semantically_similar_to--> `SQLAlchemy 2.0 Async`  [INFERRED] [semantically similar]
  app/README.md → MELHORIAS.md
- `App FastAPI User Registration Service` --semantically_similar_to--> `FastAPI REST User API`  [INFERRED] [semantically similar]
  app/README.md → MELHORIAS.md
- `Alembic Migrations` --semantically_similar_to--> `Alembic Migrations`  [INFERRED] [semantically similar]
  app/README.md → MELHORIAS.md
- `Intentionally Empty 0001 Baseline Revision` --semantically_similar_to--> `Empty 0001 Baseline Migration`  [INFERRED] [semantically similar]
  app/README.md → MELHORIAS.md
- `criar_usuario()` --references--> `post`  [EXTRACTED]
  app/src/api/usuarios.py → asciiart-load-test.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Persistence Modernization Flow** — melhorias_persistencia_memoria, melhorias_usuario_model, melhorias_sqlalchemy_async, melhorias_alembic_migracoes, melhorias_cd_pipeline [EXTRACTED 1.00]
- **Cloud Run Connection Budget** — melhorias_cloud_run, app_readme_cloud_run_pool, app_readme_pool_config, app_readme_database_url [INFERRED 0.85]
- **CI/CD and Container Hardening** — melhorias_ci_pipeline, melhorias_cd_pipeline, melhorias_dockerfile, melhorias_dockerignore, melhorias_alembic_migracoes [EXTRACTED 1.00]

## Communities (33 total, 24 thin omitted)

### Community 0 - "Configuration and Deployment"
Cohesion: 0.07
Nodes (44): Alembic Migrations, Nested alembic.ini Configuration, Artillery Load Test, Cloud Run Instance Connection Budget, Settings Module, DATABASE_URL Configuration, Environment File Handling, User and Health Endpoints (+36 more)

### Community 1 - "User API Endpoints"
Cohesion: 0.10
Nodes (16): criar_usuario(), listar_usuarios(), obter_usuario(), EmailJaCadastrado, RespostaDoUsuario, UsuarioNaoEncontrado, Dominio, UnidadeDeTrabalho (+8 more)

### Community 2 - "User Domain and Repositories"
Cohesion: 0.08
Nodes (10): Usuario, buscar_usuario_por_email(), buscar_usuario_por_id(), listar_usuarios(), salvar_usuario(), UsuarioLeituraRepositorio, UsuarioRepositorio, buscar_usuario_por_email() (+2 more)

### Community 3 - "CD Pipeline Workflow"
Cohesion: 0.07
Nodes (33): name, needs, runs-on, steps, run, env, D_PASS, D_USER (+25 more)

### Community 4 - "Health and Session Management"
Cohesion: 0.11
Nodes (7): saude(), Session, lifespan(), database_url(), db_session(), postgres_container(), reset_usuarios()

### Community 5 - "Alembic Migration Environment"
Cohesion: 0.11
Nodes (6): do_run_migrations(), run_async_migrations(), run_migrations_offline(), run_migrations_online(), upgrade(), Base

### Community 6 - "Artillery Load Testing"
Cohesion: 0.09
Nodes (22): expression, config, phases, plugins, target, conditions, thresholds, post (+14 more)

### Community 7 - "CI Pipeline Workflow"
Cohesion: 0.09
Nodes (21): run, jobs, test, name, branches, branches, working-directory, name (+13 more)

### Community 8 - "Settings and Unit Tests"
Cohesion: 0.19
Nodes (5): get_settings(), Settings, test_pool_settings_are_overridable_by_environment(), test_settings_keep_the_query_string(), test_settings_use_the_async_postgres_dialect()

## Knowledge Gaps
- **8 isolated node(s):** `app`, `Concurrent Request Race Condition`, `AGENTS.md Simplicity Rule`, `Manual Email Regex Validation`, `Duplicated Session Management` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 144 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `criar_usuario()` connect `User API Endpoints` to `Artillery Load Testing`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Usuario` (e.g. with `buscar_usuario_por_email()` and `buscar_usuario_por_id()`) actually correct?**
  _`Usuario` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `app`, `Concurrent Request Race Condition`, `AGENTS.md Simplicity Rule` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Configuration and Deployment` be split into smaller, more focused modules?**
  _Cohesion score 0.06570048309178744 - nodes in this community are weakly interconnected._
- **Why does `post` connect `Artillery Load Testing` to `User API Endpoints`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `UnidadeDeTrabalho` (e.g. with `criar_usuario()` and `listar_usuarios()`) actually correct?**
  _`UnidadeDeTrabalho` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `User API Endpoints` be split into smaller, more focused modules?**
  _Cohesion score 0.10365853658536585 - nodes in this community are weakly interconnected._