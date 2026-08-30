FROM python:3.13-slim

# Els print() del worker han de sortir a `docker logs` sense buffer
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

# Les dependencies viuen al pyproject/uv.lock de l'arrel del repo,
# per aixo el context del build es l'arrel i no lol-tracker/
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY lol-tracker/ ./

EXPOSE 8766

CMD ["/app/.venv/bin/uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8766"]
