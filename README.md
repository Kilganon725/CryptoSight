# CryptoSight

CryptoSight is a cryptocurrency market analysis and price prediction platform focused on BTC with room for ETH and other assets.

## Repository Layout

- `app/`: FastAPI backend
- `frontend/`: Vue 3 + TypeScript dashboard scaffold
- `docs/`: thesis-ready architecture, ER, API, and deployment materials
- `sql/schema.sql`: MySQL DDL
- `docker-compose.yml`: backend + MySQL stack

## Backend

### Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Default database

If `DATABASE_URL` is not set, the app uses SQLite at `./cryptosight.db`.

For MySQL:

```bash
export DATABASE_URL='mysql+pymysql://user:password@127.0.0.1:3306/cryptosight?charset=utf8mb4'
```

### Key endpoints

- `GET /api/health`
- `GET /api/btc/history`
- `GET /api/market/overview`
- `GET /api/macro`
- `GET /api/sentiment`
- `GET /api/factors`
- `POST /api/predict`
- `POST /api/train`
- `GET /api/model-performance`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite config proxies `/api` to `http://localhost:8000`.

## Docs

- `docs/architecture.md`
- `docs/er-diagram.md`
- `docs/api.md`
- `docs/deployment.md`
- `docs/thesis-materials.md`

## Notes

- The backend seeds demo data automatically when a dataset is empty.
- Optional ML libraries fall back to simpler models when not installed.
- In production, replace demo seeding with real collectors and scheduled retraining jobs.
