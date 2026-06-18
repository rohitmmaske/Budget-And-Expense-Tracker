# DATABASE REPORT

**Project:** Budget Bloom
**Date:** 2026-06-18

---

## 1. Database Configuration

| Setting | Value |
|---------|-------|
| Default (no env set) | SQLite — `backend/budget_app.db` |
| Production target | PostgreSQL via Supabase |
| ORM | SQLAlchemy 2.0 (DeclarativeBase, mapped_column) |
| Migration tool | None — `Base.metadata.create_all()` on startup |

---

## 2. Tables

### `users`
| Column | Type | Constraints |
|--------|------|-------------|
| id | VARCHAR(36) | PRIMARY KEY, default=uuid4() |
| full_name | VARCHAR(120) | NOT NULL |
| email | VARCHAR(255) | UNIQUE, INDEX, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL, default=utc_now() |

### `incomes`
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY, INDEX |
| user_id | VARCHAR(36) | FK → users.id ON DELETE CASCADE, INDEX, NOT NULL |
| amount | NUMERIC(12,2) | NOT NULL |
| source | VARCHAR(80) | NOT NULL, default='Salary' |
| note | VARCHAR(255) | NULLABLE |
| income_date | DATE | NOT NULL, default=today |
| created_at | TIMESTAMPTZ | NOT NULL, default=utc_now() |

### `expenses`
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY, INDEX |
| user_id | VARCHAR(36) | FK → users.id ON DELETE CASCADE, INDEX, NOT NULL |
| amount | NUMERIC(12,2) | NOT NULL |
| category | VARCHAR(80) | NOT NULL, INDEX |
| title | VARCHAR(120) | NOT NULL |
| note | VARCHAR(255) | NULLABLE |
| expense_date | DATE | NOT NULL, default=today |
| created_at | TIMESTAMPTZ | NOT NULL, default=utc_now() |

### `savings`
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY, INDEX |
| user_id | VARCHAR(36) | FK → users.id ON DELETE CASCADE, INDEX, NOT NULL |
| amount | NUMERIC(12,2) | NOT NULL |
| goal_name | VARCHAR(120) | NOT NULL, default='General Savings' |
| note | VARCHAR(255) | NULLABLE |
| saving_date | DATE | NOT NULL, default=today |
| created_at | TIMESTAMPTZ | NOT NULL, default=utc_now() |

### `budgets`
| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY, INDEX |
| user_id | VARCHAR(36) | FK → users.id ON DELETE CASCADE, INDEX, NOT NULL |
| category | VARCHAR(80) | NOT NULL |
| monthly_limit | NUMERIC(12,2) | NOT NULL |
| month | VARCHAR(7) | NOT NULL (YYYY-MM format) |
| created_at | TIMESTAMPTZ | NOT NULL, default=utc_now() |
| — | UNIQUE | (user_id, category, month) |

---

## 3. Indexes

| Index Name | Table | Column(s) |
|------------|-------|-----------|
| ix_users_email | users | email |
| ix_incomes_user_id | incomes | user_id |
| ix_expenses_user_id | expenses | user_id |
| ix_expenses_category | expenses | category |
| ix_savings_user_id | savings | user_id |
| ix_budgets_user_id | budgets | user_id |
| uq_budget_user_category_month | budgets | (user_id, category, month) UNIQUE |

---

## 4. Connection Validation

### SQLite (local dev)
- Auto-created at `backend/budget_app.db` on first startup ✅
- All 5 tables created successfully ✅
- `pool_pre_ping=True` — stale connection detection active ✅
- `check_same_thread=False` — required for SQLite in multi-threaded ASGI ✅

### PostgreSQL / Supabase
- Driver resolution: psycopg v3 → psycopg2 fallback (fixed in `database.py`) ✅
- URL normalization handles `postgres://`, `postgresql://`, and explicit driver prefixes ✅
- `pool_pre_ping=True` — reconnects after idle timeout ✅

---

## 5. Migration Status

| Aspect | Status |
|--------|--------|
| Formal migration tool (Alembic) | Not configured |
| Auto-create on startup | ✅ Active (`create_all`) |
| Risk | Schema changes require manual table alteration on existing databases |

**Recommendation:** For production use, integrate Alembic:
```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## 6. Schema Consistency — ORM vs SQL

The `supabase/schema.sql` file is an **optional** manual alternative to auto-creation.
Consistency check:

| Table | In schema.sql | In models.py | Match |
|-------|--------------|--------------|-------|
| users | ✅ | ✅ | ✅ |
| incomes | ✅ | ✅ | ✅ |
| expenses | ✅ | ✅ | ✅ |
| savings | ✅ | ✅ | ✅ |
| budgets | ✅ | ✅ | ✅ |

Column-level comparison: **all columns match** across both files.

---

## 7. Supabase Setup Instructions

### Option A — Automatic (recommended)
1. Create a Supabase project at https://supabase.com
2. Go to Project Settings → Database → Connection String (Direct)
3. Copy the connection string
4. Set in `backend/.env`:
   ```env
   DATABASE_URL=postgresql://postgres:PASSWORD@db.YOURREF.supabase.co:5432/postgres
   ```
5. Start the server — tables are created automatically

### Option B — Manual SQL
1. Open Supabase Dashboard → SQL Editor
2. Paste and run contents of `supabase/schema.sql`
3. Set `DATABASE_URL` in `.env` and start the server

---

## 8. Data Integrity

| Rule | Enforced By |
|------|-------------|
| amount > 0 | Pydantic `Field(gt=0)` + SQL CHECK (schema.sql only) |
| Valid YYYY-MM month format | Pydantic `field_validator` regex + custom validator |
| Unique budget per user+category+month | DB UNIQUE constraint + ORM upsert logic |
| Cascade delete (user → all records) | FK `ON DELETE CASCADE` |
| Email uniqueness | DB UNIQUE constraint + application-level check |
