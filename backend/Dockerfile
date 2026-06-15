FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir "poetry>=2.0.0,<3.0.0"

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry lock && poetry install --no-interaction --no-ansi

COPY app/ app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
