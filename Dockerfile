FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY src ./src
COPY run_astra.sh ./run_astra.sh

RUN chmod +x run_astra.sh

EXPOSE 8000
EXPOSE 8501

CMD ["bash", "run_astra.sh"]
