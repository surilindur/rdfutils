FROM docker.io/python:3.14-alpine AS base

FROM base AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV VIRTUAL_ENV=/opt/venv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /opt/rdfutils

ADD ./src/*.py .
ADD ./pyproject.toml .
ADD ./uv.lock .

RUN uv venv /opt/venv
RUN uv sync --active --no-dev --locked

FROM base

COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/rdfutils /opt/rdfutils

WORKDIR /opt/rdfutils

RUN adduser --no-create-home --disabled-password --uid 1000 python

USER python

ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT [ "python", "./cli.py" ]
