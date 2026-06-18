"""
schemas.py
----------
Pydantic v2 request/response schemas.

Changes from original:
- Added user_id to IncomeOut, ExpenseOut, SavingOut, BudgetOut (needed for API consumers).
- Used Optional[str] instead of str | None for Python < 3.10 compatibility notes
  (Python 3.11 supports both; kept Optional for broader readability).
- Added missing user_id field on all *Out schemas so API responses include ownership info.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: EmailStr
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Income / Salary
# ---------------------------------------------------------------------------

class IncomeCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    source: str = Field(default="Salary", max_length=80)
    note: Optional[str] = Field(default=None, max_length=255)
    income_date: date = Field(default_factory=date.today)


class IncomeOut(IncomeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------

class ExpenseCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    category: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=120)
    note: Optional[str] = Field(default=None, max_length=255)
    expense_date: date = Field(default_factory=date.today)


class ExpenseOut(ExpenseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

class SavingCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    goal_name: str = Field(default="General Savings", max_length=120)
    note: Optional[str] = Field(default=None, max_length=255)
    saving_date: date = Field(default_factory=date.today)


class SavingOut(SavingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class BudgetCreate(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    monthly_limit: Decimal = Field(gt=0)
    month: str = Field(pattern=r"^\d{4}-\d{2}$")

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        year, month = value.split("-")
        if not (1 <= int(month) <= 12):
            raise ValueError("month must be between 01 and 12")
        if int(year) < 2000:
            raise ValueError("year must be 2000 or later")
        return value


class BudgetOut(BudgetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Dashboard / Charts
# ---------------------------------------------------------------------------

class SummaryOut(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    total_savings: Decimal
    balance_after_expense: Decimal
    available_balance: Decimal
    highest_category: Optional[str] = None
    highest_category_amount: Decimal = Decimal("0.00")


class CategoryChartItem(BaseModel):
    category: str
    total: Decimal


class MonthlyChartItem(BaseModel):
    month: str
    income: Decimal
    expense: Decimal
    savings: Decimal
