# Budget Bloom - Expense & Budget Website

A full-stack expense and budget tracker using **FastAPI**, **Supabase/Postgres**, **JWT Auth**, **Postman**, and your color palette:

- `#FDF4AF`
- `#A5E9DD`
- `#6FBEB2`
- `#34908B`

## Features

- Register and login with JWT auth
- Add salary/income multiple times
- Add expenses and automatically see balance reduced
- Add savings goals
- Add monthly budgets by category
- Dashboard cards: income, expenses, savings, available balance
- Category spending chart
- Monthly income vs expense vs savings chart
- Postman collection included
- Supabase ready through `DATABASE_URL`
- SQLite fallback for local testing

## Project Structure

```txt
expense-budget-fastapi-supabase/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── deps.py
│   │   ├── routes_auth.py
│   │   └── routes_finance.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── postman/
│   └── Expense_Budget_API.postman_collection.json
├── supabase/
│   └── schema.sql
├── run_backend_windows.bat
├── run_backend_mac_linux.sh
└── README.md
```

## Run on Windows

Open terminal inside the project folder and run:

```bat
run_backend_windows.bat
```

Then open:

```txt
http://127.0.0.1:8000
```

API docs:

```txt
http://127.0.0.1:8000/docs
```

## Manual Run Commands

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Install packages:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy env file:

```bash
copy .env.example .env
```

Mac/Linux:

```bash
cp .env.example .env
```

Run server:

```bash
python -m uvicorn app.main:app --reload
```

## Supabase Setup

### Option 1: Use auto table creation

1. Create a project on Supabase.
2. Go to **Project Settings > Database**.
3. Copy the database connection string.
4. Paste it in `backend/.env` as `DATABASE_URL`.
5. Run the FastAPI server. Tables are created automatically.

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
SECRET_KEY=make-this-long-and-random
```

### Option 2: Use SQL Editor

Open Supabase SQL Editor and run:

```txt
supabase/schema.sql
```

Then run the backend normally.

## Important Supabase Note

If Supabase gives you a URL starting with `postgresql://`, this project automatically converts it to `postgresql+psycopg://` in code.

For pooler URLs, this format also works:

```env
DATABASE_URL=postgresql+psycopg://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

## Postman

Import this file in Postman:

```txt
postman/Expense_Budget_API.postman_collection.json
```

The collection has variables:

- `base_url` = `http://127.0.0.1:8000`
- `token` = automatically saved after register/login

Flow:

1. Register
2. Login
3. Add Salary
4. Add Expense
5. Add Savings
6. Check Summary

## API Endpoints

### Auth

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login and get JWT |
| GET | `/auth/me` | Get current user |

### Finance

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/finance/salary` | Add salary or extra income |
| GET | `/finance/salary` | List income records |
| POST | `/finance/expenses` | Add expense |
| GET | `/finance/expenses` | List expenses |
| DELETE | `/finance/expenses/{id}` | Delete expense |
| POST | `/finance/savings` | Add savings |
| GET | `/finance/savings` | List savings |
| DELETE | `/finance/savings/{id}` | Delete saving |
| POST | `/finance/budgets` | Add/update monthly budget |
| GET | `/finance/budgets` | List budgets |
| DELETE | `/finance/budgets/{id}` | Delete budget |
| GET | `/finance/summary` | Dashboard totals |
| GET | `/finance/charts/categories` | Category chart data |
| GET | `/finance/charts/monthly` | Monthly chart data |

## How Balance Works

```txt
Balance after expenses = total income - total expenses
Available balance = total income - total expenses - total savings
```

So savings are treated as money separated for future goals.

## Default Local Database

If you do not set `DATABASE_URL`, the app uses:

```txt
backend/budget_app.db
```

That means you can test everything locally first. When Supabase is ready, add your Supabase URL to `.env`.
