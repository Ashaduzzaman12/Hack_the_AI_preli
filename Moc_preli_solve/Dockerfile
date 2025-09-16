
# Production image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /srv
COPY . /srv

# Create persistent volume path
RUN mkdir -p /data

RUN pip install --no-cache-dir fastapi uvicorn gunicorn pydantic[dotenv] pytest httpx

EXPOSE 8000

# Use gunicorn with uvicorn workers for concurrency
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--timeout", "90"]
