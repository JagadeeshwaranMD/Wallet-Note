# Wallet Note — Personal Finance, Money Tracking & Debt Management System

**Wallet Note** is a web-based personal financial ledger and debt tracking application integrated directly with **Zoho Catalyst Data Store** under the **Wallet-Note** project (`41833000000087004`).

---

## 🌟 Key Features & Functional Modules

### 1. Consolidated Financial Dashboard (FR-01)
- Dynamic calculation of **Total Income**, **Total Expenses**, **Net Income**, and **Available Funds**.
- **Debt Position Tracking**: Total Borrowed, Total Repaid, Outstanding Payables vs Total Lent, Total Collected, Outstanding Receivables.
- Interactive **Monthly Trend Comparison** (Income vs Expense) & **Expense Category Breakdown** charts powered by Chart.js.
- Real-time **Pending Repayments & Collections** alert table.

### 2. Income Management (FR-02)
- Record income with unique reference numbers (`INC-YYYYMMDD-XXXX`), income sources (Salary, Freelance, Business, etc.), payment accounts, and transaction dates.
- Automatic account balance increment.
- Full CRUD operations with search and date filters.

### 3. Expense Management (FR-03)
- Detailed expense logging with unique references (`EXP-YYYYMMDD-XXXX`), categories (Food & Dining, Transportation, Utilities, Medical, etc.), payment methods, and notes.
- Automatic account balance decrement and balance recalculation on edits or deletions.

### 4. Borrowed Money Management (FR-04)
- Track all money borrowed from lenders with reference (`BOR-YYYYMMDD-XXXX`), borrowing date, due date, receiving account, and interest notes.
- Supports multi-stage partial repayments (`Pending`, `Partially Paid`, `Completed`, `Overdue`).
- **Core Financial Rule**: Borrowed principal is treated as liability, not ordinary income.

### 5. Lent Money Management (FR-05)
- Track all loans given to borrowers with reference (`LND-YYYYMMDD-XXXX`), disbursement account, expected return date, and terms.
- Supports multi-stage partial collections (`Pending`, `Partially Received`, `Completed`, `Overdue`).
- **Core Financial Rule**: Lent principal is treated as asset receivable, not ordinary expense.

### 6. Repayment & Collection Settlements (FR-06)
- Centralized settlement workflow linked directly to loan references.
- Validates payment amounts against current outstanding balance.
- Automatic recalculation of loan status and account balances.

### 7. People Directory & Contact Management (FR-07)
- Maintain centralized records of all lenders and borrowers.
- Instant overview of money given, to collect, money borrowed, to pay, and net balance.
- Safe deletion policy preventing loss of historical records.

### 8. Dedicated Person-wise Personal Ledger (FR-08)
- Complete two-way statement for any selected individual:
  - **Receivables Summary**: Total Given, Collected, Remaining.
  - **Payables Summary**: Total Borrowed, Repaid, Remaining.
  - **Net Financial Position Badge**: Shows whether they owe you, you owe them, or fully settled.
  - Unified chronological timeline of all borrowings, lendings, and settlement payments.
  - Print/PDF export friendly format.

### 9. Unified Transaction Register (FR-09)
- Centralized chronological register with filtering by classification, account, person, date range, and amount.
- Export all transactions to CSV format with one click.

### 10. Multi-Account Management & Internal Transfers (FR-10)
- Manage Cash, Savings Bank Accounts, Current Accounts, UPI, and Digital Wallets.
- Execute internal fund transfers (`TRF-YYYYMMDD-XXXX`) without altering total net worth or skewing income/expense totals.
- Safe deactivation preventing deactivation of accounts with active balances.

### 11. Reminder Management (FR-11)
- Real-time detection of overdue obligations and upcoming due dates (within 7 days).
- Navbar notification badge with one-click navigation to settle dues.

### 12. 13 Financial Reports & Analytics (FR-12)
1. Monthly Income Report
2. Monthly Expense Report
3. Yearly Financial Summary
4. Category-wise Expense Report
5. Income Source Report
6. Borrowed Money Report
7. Repayment Report
8. Lent Money Report
9. Collection Report
10. Outstanding Payables Report
11. Outstanding Receivables Report
12. Person-wise Ledger Report
13. Account-wise Balance Report
- All reports feature CSV export and print preview.

### 13. System Settings & Custom Categories (FR-13)
- Preference management (Currency symbol/code, Light & Dark themes).
- Custom category creator for custom income and expense types.

---

## 🗄️ Zoho Catalyst Data Store Tables

The following 12 tables and schemas have been created and configured in Zoho Catalyst for project `Wallet-Note`:

| Table Name | Catalyst Table ID | Key Columns |
|------------|-------------------|-------------|
| `accounts` | `41833000000484004` | `account_name`, `account_type`, `opening_balance`, `current_balance`, `currency`, `status` |
| `people` | `41833000000479002` | `person_ref`, `full_name`, `mobile_number`, `email`, `address`, `status` |
| `categories` | `41833000000475390` | `category_name`, `category_type`, `is_default`, `icon`, `color` |
| `incomes` | `41833000000485360` | `income_ref`, `source`, `amount`, `received_from`, `transaction_date`, `account_id` |
| `expenses` | `41833000000475749` | `expense_ref`, `category`, `amount`, `paid_to`, `transaction_date`, `account_id` |
| `borrowings` | `41833000000488001` | `borrow_ref`, `person_id`, `borrowed_amount`, `total_repaid`, `outstanding_payable`, `due_date`, `status` |
| `lendings` | `41833000000481004` | `lend_ref`, `person_id`, `lent_amount`, `total_collected`, `outstanding_receivable`, `status` |
| `loan_payments` | `41833000000476017` | `payment_ref`, `loan_type`, `loan_id`, `amount`, `payment_date`, `account_id` |
| `account_transfers` | `41833000000487108` | `transfer_ref`, `from_account_id`, `to_account_id`, `amount`, `transfer_date` |
| `transactions` | `41833000000488360` | `transaction_ref`, `transaction_date`, `transaction_type`, `amount`, `account_id` |
| `reminders` | `41833000000489001` | `reminder_type`, `related_loan_id`, `person_name`, `amount`, `due_date`, `status` |
| `app_settings` | `41833000000489360` | `setting_key`, `setting_value` |

---

## 🚀 Running the Application

### Option A: Local Python Server (Recommended for Fast Development)

Run the Python application directly:
```bash
python app.py
```
Open **[http://localhost:9000](http://localhost:9000)** in your browser.

### Option B: Zoho Catalyst CLI

Serve functions and client via Catalyst emulation:
```bash
cmd /c catalyst serve
```

### Option C: Deploy to Zoho Catalyst Cloud

Deploy to the Catalyst Development environment:
```bash
cmd /c catalyst deploy
```

---

## 🧪 Running Automated Tests

Run the financial integrity and module test suite:
```bash
python -m unittest tests/test_wallet_note.py
```
All 9 unit tests verify account reconciliation, loan status updates, multi-stage repayments/collections, transfers, and report generation.

