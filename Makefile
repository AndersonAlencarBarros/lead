.PHONY: help setup install run dev run-prod migrate upgrade downgrade current history migration mkmigration test test-quick test-ia ruff ruff-format format-check migration-check build clean redis celery docker-build docker-run docker-run-bg docker-stop

IMAGE_NAME ?= etl-python
TAG ?= local

help: ## Exibe esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup install: ## Instala dependências com Poetry
	cd app && poetry install

run dev: ## Inicia a aplicação local com reload
	cd app && poetry run uvicorn main:app --reload

run-prod: ## Inicia a aplicação em modo "produção" (porta via PORT)
	cd app && poetry run uvicorn main:app --host 0.0.0.0 --port $${PORT:-8080}

redis: ## Sobe Redis local para o Celery
	docker run --rm -p 6379:6379 redis:7-alpine

celery: ## Inicia worker Celery para respostas da IA
	cd app && poetry run celery -A infraestrutura.celery_app:celery_app worker --loglevel=info

migrate upgrade: ## Aplica migrações pendentes (alembic upgrade head)
	cd app && poetry run alembic -c src/infraestrutura/alembic/alembic.ini upgrade head

downgrade: ## Desfaz a última migração
	cd app && poetry run alembic -c src/infraestrutura/alembic/alembic.ini downgrade -1

current: ## Mostra a revisão atual do banco
	cd app && poetry run alembic -c src/infraestrutura/alembic/alembic.ini current

history: ## Mostra o histórico de migrações
	cd app && poetry run alembic -c src/infraestrutura/alembic/alembic.ini history --verbose

migration mkmigration: ## Cria nova migração com autogenerate (uso: make migration msg="sua mensagem")
	@test -n "$(msg)" || (echo "Erro: parâmetro msg é obrigatório. Use: make migration msg=\"sua mensagem\""; exit 1)
	cd app && poetry run alembic -c src/infraestrutura/alembic/alembic.ini revision --autogenerate -m "$(msg)"

test: ## Executa todos os testes com saída detalhada
	cd app && poetry run pytest -v

test-quick: ## Executa testes rapidamente
	cd app && poetry run pytest

test-ia: ## Executa testes reais contra o provedor LLM configurado
	cd app && poetry run pytest testes/integracao/ia -v

ruff: ## Verifica código com Ruff
	cd app && poetry run ruff check .

ruff-format: ## Formata código com Ruff
	cd app && poetry run ruff format .

format-check: ## Verifica formatação sem alterar arquivos
	cd app && poetry run ruff format --check .

migration-check: ## Verifica divergência entre ORM e migrações
	cd app && poetry run alembic -c src/infraestrutura/alembic/alembic.ini check

build: ## Cria pacote com Poetry
	cd app && poetry build

clean: ## Remove artefatos Python, pytest e build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	rm -rf app/build app/dist app/*.egg-info 2>/dev/null; true

docker-build: ## Builda a imagem Docker do projeto
	docker build -t $(IMAGE_NAME):$(TAG) ./app

docker-run: ## Executa a imagem Docker localmente na porta 8080
	docker run --rm -p 8080:8080 -e PORT=8080 $(IMAGE_NAME):$(TAG)

docker-run-bg: ## Executa a imagem Docker em segundo plano (nome: etl-python-app)
	docker run -d --rm --name etl-python-app -p 8080:8080 -e PORT=8080 $(IMAGE_NAME):$(TAG)

docker-stop: ## Para o container rodando em segundo plano
	docker stop etl-python-app 2>/dev/null || true
