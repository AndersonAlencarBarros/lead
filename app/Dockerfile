FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install poetry==2.5.1
COPY pyproject.toml poetry.lock README.md ./
COPY src ./src

RUN poetry config virtualenvs.create false && poetry install --no-interaction --without dev
COPY . .
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]