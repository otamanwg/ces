FROM python:3.12-slim

ARG CITY_RELEASE_SHA=unknown
ARG CITY_RELEASE_IMAGE=local
ARG CITY_RELEASE_VERSION=0.3.0

LABEL org.opencontainers.image.title="City Economic Simulator Backend" \
    org.opencontainers.image.description="Production backend image for City Economic Simulator" \
    org.opencontainers.image.revision="${CITY_RELEASE_SHA}" \
    org.opencontainers.image.version="${CITY_RELEASE_VERSION}" \
    org.opencontainers.image.ref.name="${CITY_RELEASE_IMAGE}"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY alembic.ini /app/alembic.ini
COPY backend /app/backend
COPY database/college_exams_manager.json /app/database/college_exams_manager.json

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
