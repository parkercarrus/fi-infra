# FI Infra

Deployment-ready portfolio dashboard backed by DuckDB.

## Structure

`backend/`
- FastAPI service that reads `algory.duckdb`
- Clean app modules for config, database access, analytics, and routes
- `GET /api/v1/platform` returns the frontend payload
- Daily Google Sheet refresh and forward-filled history maintenance live in `backend/api.py`
- Theoretical-position helpers live in `backend/app/services/theoretical.py`

`frontend/`
- Next.js 16 dashboard with a modular UI
- Server-rendered portfolio overview, exposure panel, and trade history table
- Configured for standalone output in production

`algory.duckdb`
- `positions`: current position snapshot
- `position_snapshots`: raw Google Sheet snapshots over time
- `position_history`: forward-filled daily history used for denser charts
- `trade_history`: filtered trade ledger used for modeled analytics

## Run Locally

Backend:
```bash
python -m backend.main
```

Frontend:
```bash
cd frontend
conda run -n base npm run dev
```

If your API is not running on `http://127.0.0.1:8000`, set:

```bash
PORTFOLIO_API_BASE_URL=http://your-api-host:8000
```

## Environment

Backend example env: [backend/.env.example](/Users/parker/Desktop/fi-infra/backend/.env.example)

Frontend example env: [frontend/.env.example](/Users/parker/Desktop/fi-infra/frontend/.env.example)

## Verification

The DuckDB verification script is:

```bash
python /Users/parker/Desktop/fi-infra/verify_trade_history.py
```

It validates the database tables and prints the live table contents to the terminal.

## Maintenance Commands

Run the daily refresh flow:

```bash
python -m backend.api daily-refresh
```

Refresh just the latest Google Sheet snapshot:

```bash
python -m backend.api refresh-sheet
```

Rebuild the forward-filled daily position history:

```bash
python -m backend.api rebuild-history
```

Reset the theoretical database from current positions:

```bash
python -m backend.api reset-theoretical
```

Add a theoretical position path:

```bash
python -m backend.api add-theoretical TICKER 2025-01-01 2025-12-31 --num-shares 10
```
