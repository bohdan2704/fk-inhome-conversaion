FROM python:3.12-slim

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FEED_API_HOST=0.0.0.0
ENV FEED_API_PORT=8000

WORKDIR /app

RUN groupadd --gid "${APP_GID}" appuser \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --create-home --shell /bin/bash appuser

COPY . /app

RUN mkdir -p /app/logs /app/feed_module/generated \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["python", "main.py"]
