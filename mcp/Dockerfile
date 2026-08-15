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
