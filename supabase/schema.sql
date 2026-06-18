-- Optional Supabase SQL schema.
-- FastAPI also creates these tables automatically on startup.
-- Use this if you want to create tables manually inside Supabase SQL Editor.

create table if not exists users (
  id varchar(36) primary key,
  full_name varchar(120) not null,
  email varchar(255) unique not null,
  password_hash varchar(255) not null,
  created_at timestamptz default now()
);

create index if not exists ix_users_email on users(email);

create table if not exists incomes (
  id bigserial primary key,
  user_id varchar(36) references users(id) on delete cascade,
  amount numeric(12, 2) not null check (amount > 0),
  source varchar(80) default 'Salary',
  note varchar(255),
  income_date date default current_date,
  created_at timestamptz default now()
);

create index if not exists ix_incomes_user_id on incomes(user_id);

create table if not exists expenses (
  id bigserial primary key,
  user_id varchar(36) references users(id) on delete cascade,
  amount numeric(12, 2) not null check (amount > 0),
  category varchar(80) not null,
  title varchar(120) not null,
  note varchar(255),
  expense_date date default current_date,
  created_at timestamptz default now()
);

create index if not exists ix_expenses_user_id on expenses(user_id);
create index if not exists ix_expenses_category on expenses(category);

create table if not exists savings (
  id bigserial primary key,
  user_id varchar(36) references users(id) on delete cascade,
  amount numeric(12, 2) not null check (amount > 0),
  goal_name varchar(120) default 'General Savings',
  note varchar(255),
  saving_date date default current_date,
  created_at timestamptz default now()
);

create index if not exists ix_savings_user_id on savings(user_id);

create table if not exists budgets (
  id bigserial primary key,
  user_id varchar(36) references users(id) on delete cascade,
  category varchar(80) not null,
  monthly_limit numeric(12, 2) not null check (monthly_limit > 0),
  month varchar(7) not null,
  created_at timestamptz default now(),
  constraint uq_budget_user_category_month unique(user_id, category, month)
);

create index if not exists ix_budgets_user_id on budgets(user_id);
