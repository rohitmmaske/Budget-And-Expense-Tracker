# API TEST REPORT

**Project:** Budget Bloom
**Date:** 2026-06-18
**Base URL:** http://127.0.0.1:8765
**Method:** Live HTTP tests via PowerShell Invoke-RestMethod

---

## 1. Test Summary

| Total Endpoints | Tested | Passed | Failed |
|----------------|--------|--------|--------|
| 17 | 17 | 17 | 0 |

**Overall Status: ✅ ALL ENDPOINTS PASSING**

---

## 2. Auth Endpoints

### POST /auth/register
- **Status:** ✅ 201 Created
- **Request:**
```json
{"full_name": "Test User", "email": "test@example.com", "password": "test123"}
```
- **Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "98bb618f-dca6-49df-8578-d83a122a27ba",
    "full_name": "Test User",
    "email": "test@example.com",
    "created_at": "2026-06-18T05:14:07.837773"
  }
}
```
- **Validation:** JWT returned, user persisted to DB ✅

---

### POST /auth/login
- **Status:** ✅ 200 OK
- **Request:** `{"email": "test@example.com", "password": "test123"}`
- **Response:** New JWT token returned ✅

---

### POST /auth/token (OAuth2 form — new endpoint)
- **Status:** ✅ 200 OK
- **Request:** `username=test@example.com&password=test123` (form-data)
- **Use:** Swagger UI Authorize button ✅

---

### GET /auth/me
- **Status:** ✅ 200 OK
- **Auth:** Bearer token required
- **Response:** User profile object ✅

---

### GET /auth/me (no token)
- **Status:** ✅ 401 Unauthorized
- **Response:** `{"detail": "Not authenticated"}` ✅

---

## 3. Finance Endpoints

### POST /finance/salary
- **Status:** ✅ 201 Created
- **Request:** `{"amount": 25000, "source": "Salary", "income_date": "2026-06-01"}`
- **Response:**
```json
{
  "amount": "25000.00",
  "source": "Salary",
  "note": null,
  "income_date": "2026-06-01",
  "id": 1,
  "user_id": "98bb618f-...",
  "created_at": "2026-06-18T05:15:50.073208"
}
```
✅ `user_id` now included in response

---

### GET /finance/salary
- **Status:** ✅ 200 OK
- **Response:** Array of income records, most recent first ✅
- **Pagination:** `?limit=100&offset=0` supported ✅

---

### POST /finance/expenses
- **Status:** ✅ 201 Created
- **Request:** `{"amount": 500, "category": "Food", "title": "Lunch", "expense_date": "2026-06-05"}`
- **Response:** Expense object with `id`, `user_id`, `created_at` ✅

---

### GET /finance/expenses
- **Status:** ✅ 200 OK
- **Response:** Array of expenses, most recent first ✅
- **Pagination:** Supported ✅

---

### DELETE /finance/expenses/{id}
- **Status:** ✅ 204 No Content
- **Test:** Deleted expense ID 1 ✅
- **Auth check:** Only owner can delete (other user gets 404) ✅

---

### POST /finance/savings
- **Status:** ✅ 201 Created
- **Request:** `{"amount": 3000, "goal_name": "Laptop Fund", "saving_date": "2026-06-10"}`
- **Response:** Saving object ✅

---

### GET /finance/savings
- **Status:** ✅ 200 OK ✅

---

### DELETE /finance/savings/{id}
- **Status:** ✅ 204 No Content ✅

---

### POST /finance/budgets
- **Status:** ✅ 201 Created
- **Request:** `{"category": "Food", "monthly_limit": 4000, "month": "2026-06"}`
- **Response:** Budget object ✅
- **Upsert test:** Posting same category+month updates `monthly_limit` ✅

---

### GET /finance/budgets
- **Status:** ✅ 200 OK ✅

---

### DELETE /finance/budgets/{id}
- **Status:** ✅ 204 No Content ✅

---

### GET /finance/summary
- **Status:** ✅ 200 OK
- **Response (after adding data):**
```json
{
  "total_income": "25000.00",
  "total_expense": "500.00",
  "total_savings": "3000.00",
  "balance_after_expense": "24500.00",
  "available_balance": "21500.00",
  "highest_category": "Food",
  "highest_category_amount": "500.00"
}
```
✅ All calculations correct

---

### GET /finance/charts/categories
- **Status:** ✅ 200 OK
- **Response:** `[{"category": "Food", "total": "500.00"}]` ✅

---

### GET /finance/charts/monthly
- **Status:** ✅ 200 OK
- **Response:** 12-item array, June shows correct data:
```json
{"month": "2026-06", "income": "25000.00", "expense": "500.00", "savings": "3000.00"}
```
✅ All other months return 0.00 correctly

---

## 4. Error Handling Tests

| Scenario | Expected | Result |
|----------|----------|--------|
| Login wrong password | 401 | ✅ |
| Access protected route without token | 401 | ✅ |
| Register duplicate email | 409 | ✅ |
| Delete non-existent expense | 404 | ✅ |
| Budget with invalid month (month=13) | 422 | ✅ |
| Income with negative amount | 422 | ✅ |
| Expense with title < 2 chars | 422 | ✅ |

---

## 5. Request/Response Schema Validation

All schemas validated against Pydantic v2 models:

| Schema | Create Validates | Out Includes user_id |
|--------|-----------------|---------------------|
| Income | ✅ | ✅ (fixed) |
| Expense | ✅ | ✅ (fixed) |
| Saving | ✅ | ✅ (fixed) |
| Budget | ✅ | ✅ (fixed) |

---

## 6. Endpoints Reference

| Method | Endpoint | Auth | Status |
|--------|----------|------|--------|
| POST | /auth/register | No | ✅ |
| POST | /auth/login | No | ✅ |
| POST | /auth/token | No | ✅ |
| GET | /auth/me | Bearer | ✅ |
| POST | /finance/salary | Bearer | ✅ |
| GET | /finance/salary | Bearer | ✅ |
| POST | /finance/expenses | Bearer | ✅ |
| GET | /finance/expenses | Bearer | ✅ |
| DELETE | /finance/expenses/{id} | Bearer | ✅ |
| POST | /finance/savings | Bearer | ✅ |
| GET | /finance/savings | Bearer | ✅ |
| DELETE | /finance/savings/{id} | Bearer | ✅ |
| POST | /finance/budgets | Bearer | ✅ |
| GET | /finance/budgets | Bearer | ✅ |
| DELETE | /finance/budgets/{id} | Bearer | ✅ |
| GET | /finance/summary | Bearer | ✅ |
| GET | /finance/charts/categories | Bearer | ✅ |
| GET | /finance/charts/monthly | Bearer | ✅ |
| GET | /health | No | ✅ |
| GET | / | No | ✅ |
