FROM python:3.12-slim-bookworm

ARG VERSION=0.4.1

LABEL org.opencontainers.image.title="sdai-biosteam-mcp" \
      org.opencontainers.image.description="BioSTEAM/QSDsan MCP server for SDAI research workflows" \
      org.opencontainers.image.version="${VERSION}"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    graphviz \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md engine.py ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app /home/mcp
USER mcp

ENV HOME=/home/mcp \
    TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_HTTP_PATH=/mcp \
    PYTHONUNBUFFERED=1

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)" || exit 1

CMD ["python", "-m", "src"]
