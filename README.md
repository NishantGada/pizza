# 🍕 pizza

A personal, multi-user budgeting app. Enter your post-tax income for a pay cycle
and it slices it into savings, retirement, HSA, your own categories, and whatever
is left as your spending limit.

## Budget model

For an entered post-tax paycheck `P` in a cycle:

- **Savings** = 60% of `P` _(editable)_
- **401(k)** = 1% of `P` _(editable)_
- **HSA** = $50 per cycle _(editable; $100/month split over two cycles)_
- **Categories** = the sum of your per-cycle allocations (fitness, vacation, …)
- **Available spending** = `P − savings − 401k − HSA − Σ(categories)`

Rule percentages/amounts are snapshotted onto each pay cycle when it's created,
so editing your settings later never rewrites past cycles.

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | React + TypeScript + Vite + Tailwind CSS, urql GraphQL client |
| Backend  | FastAPI + Strawberry GraphQL, async SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL (Homebrew PG16, port 5433) |
| Auth     | Self-managed JWT (email/password), row-level ownership |

## Layout

```
pizza/
├── backend/    FastAPI + GraphQL API
└── frontend/   React + Vite client
```

## Getting started

### Database (run yourself)

```bash
createdb -p 5433 pizza          # or: psql -p 5433 -c "CREATE DATABASE pizza;"
```

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set a real JWT_SECRET
alembic revision --autogenerate -m "initial schema"   # generates migration
alembic upgrade head            # run yourself
uvicorn app.main:app --reload   # http://localhost:8000/graphql
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev                     # http://localhost:5173
```
