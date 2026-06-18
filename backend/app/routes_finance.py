"""
routes_finance.py
-----------------
Financial CRUD endpoints: salary/income, expenses, savings, budgets,
summary dashboard, and chart data.

Changes from original:
- Added missing DELETE endpoints for savings and budgets (were present but
  lacked HTTP method tags in original Postman — confirmed correct here).
- Added pagination (limit/offset) to list endpoints to prevent large payloads.
- Improved error messages on 404 responses.
- money() helper moved here from inline usage; handles None safely.
- All list endpoints now return most-recent-first ordering.
- Budget upsert uses explicit update instead of relying on session state.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user
from .models import Budget, Expense, Income, Saving, User
from .schemas import (
    BudgetCreate,
    BudgetOut,
    CategoryChartItem,
    ExpenseCreate,
    ExpenseOut,
    IncomeCreate,
    IncomeOut,
    MonthlyChartItem,
    SavingCreate,
    SavingOut,
    SummaryOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finance", tags=["Finance"])

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500


def money(value) -> Decimal:
    """Safely convert any numeric value (or None) to a 2-dp Decimal."""
    return Decimal(value or 0).quantize(Decimal("0.01"))


# ---------------------------------------------------------------------------
# Income / Salary
# ---------------------------------------------------------------------------

@router.post(
    "/salary",
    response_model=IncomeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a salary or income entry",
)
def add_salary(
    payload: IncomeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Income:
    income = Income(user_id=current_user.id, **payload.model_dump())
    db.add(income)
    db.commit()
    db.refresh(income)
    logger.info("Income added for user %s: %.2f", current_user.id, income.amount)
    return income


@router.get(
    "/salary",
    response_model=list[IncomeOut],
    summary="List all income/salary records",
)
def list_salary(
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Income]:
    return db.scalars(
        select(Income)
        .where(Income.user_id == current_user.id)
        .order_by(Income.income_date.desc(), Income.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------

@router.post(
    "/expenses",
    response_model=ExpenseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add an expense",
)
def add_expense(
    payload: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Expense:
    expense = Expense(user_id=current_user.id, **payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    logger.info("Expense added for user %s: %.2f (%s)", current_user.id, expense.amount, expense.category)
    return expense


@router.get(
    "/expenses",
    response_model=list[ExpenseOut],
    summary="List all expenses",
)
def list_expenses(
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Expense]:
    return db.scalars(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()


@router.delete(
    "/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense",
)
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    expense = db.get(Expense, expense_id)
    if not expense or expense.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense {expense_id} not found",
        )
    db.delete(expense)
    db.commit()


# ---------------------------------------------------------------------------
# Savings
# ---------------------------------------------------------------------------

@router.post(
    "/savings",
    response_model=SavingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a saving entry",
)
def add_saving(
    payload: SavingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Saving:
    saving = Saving(user_id=current_user.id, **payload.model_dump())
    db.add(saving)
    db.commit()
    db.refresh(saving)
    return saving


@router.get(
    "/savings",
    response_model=list[SavingOut],
    summary="List all savings",
)
def list_savings(
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Saving]:
    return db.scalars(
        select(Saving)
        .where(Saving.user_id == current_user.id)
        .order_by(Saving.saving_date.desc(), Saving.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()


@router.delete(
    "/savings/{saving_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saving entry",
)
def delete_saving(
    saving_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    saving = db.get(Saving, saving_id)
    if not saving or saving.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saving {saving_id} not found",
        )
    db.delete(saving)
    db.commit()


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------

@router.post(
    "/budgets",
    response_model=BudgetOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a monthly budget for a category",
)
def add_or_update_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Budget:
    existing = db.scalar(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.category == payload.category,
            Budget.month == payload.month,
        )
    )
    if existing:
        existing.monthly_limit = payload.monthly_limit
        db.commit()
        db.refresh(existing)
        return existing

    budget = Budget(user_id=current_user.id, **payload.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get(
    "/budgets",
    response_model=list[BudgetOut],
    summary="List all budgets",
)
def list_budgets(
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Budget]:
    return db.scalars(
        select(Budget)
        .where(Budget.user_id == current_user.id)
        .order_by(Budget.month.desc(), Budget.category.asc())
        .limit(limit)
        .offset(offset)
    ).all()


@router.delete(
    "/budgets/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget",
)
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    budget = db.get(Budget, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget {budget_id} not found",
        )
    db.delete(budget)
    db.commit()


# ---------------------------------------------------------------------------
# Summary dashboard
# ---------------------------------------------------------------------------

@router.get(
    "/summary",
    response_model=SummaryOut,
    summary="Dashboard totals — income, expense, savings, balance",
)
def summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SummaryOut:
    uid = current_user.id

    total_income = money(
        db.scalar(select(func.sum(Income.amount)).where(Income.user_id == uid))
    )
    total_expense = money(
        db.scalar(select(func.sum(Expense.amount)).where(Expense.user_id == uid))
    )
    total_savings = money(
        db.scalar(select(func.sum(Saving.amount)).where(Saving.user_id == uid))
    )

    top = db.execute(
        select(Expense.category, func.sum(Expense.amount).label("total"))
        .where(Expense.user_id == uid)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .limit(1)
    ).first()

    return SummaryOut(
        total_income=total_income,
        total_expense=total_expense,
        total_savings=total_savings,
        balance_after_expense=money(total_income - total_expense),
        available_balance=money(total_income - total_expense - total_savings),
        highest_category=top[0] if top else None,
        highest_category_amount=money(top[1]) if top else Decimal("0.00"),
    )


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

@router.get(
    "/charts/categories",
    response_model=list[CategoryChartItem],
    summary="Expense totals grouped by category",
)
def category_chart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategoryChartItem]:
    rows = db.execute(
        select(Expense.category, func.sum(Expense.amount).label("total"))
        .where(Expense.user_id == current_user.id)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    ).all()
    return [CategoryChartItem(category=row[0], total=money(row[1])) for row in rows]


@router.get(
    "/charts/monthly",
    response_model=list[MonthlyChartItem],
    summary="Monthly income vs expense vs savings for the current year",
)
def monthly_chart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MonthlyChartItem]:
    uid = current_user.id
    current_year = date.today().year
    rows: list[MonthlyChartItem] = []

    for month_num in range(1, 13):
        income = money(
            db.scalar(
                select(func.sum(Income.amount)).where(
                    Income.user_id == uid,
                    extract("year", Income.income_date) == current_year,
                    extract("month", Income.income_date) == month_num,
                )
            )
        )
        expense = money(
            db.scalar(
                select(func.sum(Expense.amount)).where(
                    Expense.user_id == uid,
                    extract("year", Expense.expense_date) == current_year,
                    extract("month", Expense.expense_date) == month_num,
                )
            )
        )
        savings = money(
            db.scalar(
                select(func.sum(Saving.amount)).where(
                    Saving.user_id == uid,
                    extract("year", Saving.saving_date) == current_year,
                    extract("month", Saving.saving_date) == month_num,
                )
            )
        )
        rows.append(
            MonthlyChartItem(
                month=f"{current_year}-{month_num:02d}",
                income=income,
                expense=expense,
                savings=savings,
            )
        )
    return rows
