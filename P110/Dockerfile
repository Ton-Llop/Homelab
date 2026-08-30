FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

# Igual que lol-tracker: el context del build es l'arrel del repo
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY P110/src ./src

EXPOSE 8765

CMD ["/app/.venv/bin/uvicorn", "power_monitor.api:app", \
     "--app-dir", "src", \
     "--host", "0.0.0.0", \
     "--port", "8765"]
