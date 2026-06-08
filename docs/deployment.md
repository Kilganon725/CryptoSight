# Deployment Guide

## Local Development

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run the API:

```bash
uvicorn app.main:app --reload
```

## MySQL Deployment

Set `DATABASE_URL`:

```bash
export DATABASE_URL='mysql+pymysql://cryptosight:cryptosight@127.0.0.1:3306/cryptosight?charset=utf8mb4'
```

## Docker

Build and run:

```bash
docker compose up --build
```

## Notes

- The backend seeds demo data automatically on first use.
- For production, replace demo seeding with scheduled ingestion jobs and real API collectors.
