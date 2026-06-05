FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend ./
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core unzip curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY scripts/fetch-dejavu-fonts.sh ./scripts/fetch-dejavu-fonts.sh
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts
COPY tests ./tests
COPY pytest.ini ./

RUN bash ./scripts/fetch-dejavu-fonts.sh

# В production backend раздаёт SPA из frontend/dist.
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8000
ENV PYTHONPATH=/app

RUN chmod +x /app/scripts/docker-entrypoint.sh

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
