FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FEED_API_HOST=0.0.0.0
ENV FEED_API_PORT=8000

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY . /app

RUN mkdir -p /app/logs /app/feed_module/generated \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["python", "-m", "api"]
