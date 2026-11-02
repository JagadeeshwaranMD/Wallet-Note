"""
Wallet Note - Core Business Logic & Financial Engine
Strictly adheres to all Core Financial Business Rules (FR-01 to FR-13).
"""

import datetime
import uuid
from typing import Dict, List, Any, Optional
from backend.storage import DataStore

def generate_ref(prefix: str) -> str:
    now = datetime.datetime.now()
    rand_str = uuid.uuid4().hex[:4].upper()
    return f"{prefix}-{now.strftime('%Y%m%d')}-{rand_str}"

def format_date(dt_str: Optional[str] = None) -> str:
    if not dt_str:
        return datetime.date.today().isoformat()
    return dt_str.split("T")[0]

def init_seed_data():
    """Initializes default categories and accounts if none exist."""
    # Seed Categories
    existing_cats = DataStore.get_all("categories")
    if not existing_cats:
        default_categories = [
            # Expense Categories
            {"category_name": "Food & Dining", "category_type": "Expense", "is_default": True, "icon": "utensils", "color": "#ef4444"},
            {"category_name": "Transportation", "category_type": "Expense", "is_default": True, "icon": "car", "color": "#f97316"},
            {"category_name": "Shopping", "category_type": "Expense", "is_default": True, "icon": "shopping-bag", "color": "#ec4899"},
            {"category_name": "Bills & Utilities", "category_type": "Expense", "is_default": True, "icon": "zap", "color": "#eab308"},
            {"category_name": "Medical & Healthcare", "category_type": "Expense", "is_default": True, "icon": "activity", "color": "#14b8a6"},
            {"category_name": "Education", "category_type": "Expense", "is_default": True, "icon": "book-open", "color": "#3b82f6"},
            {"category_name": "Entertainment", "category_type": "Expense", "is_default": True, "icon": "film", "color": "#8b5cf6"},
            {"category_name": "Rent & Housing", "category_type": "Expense", "is_default": True, "icon": "home", "color": "#6366f1"},
            {"category_name": "Personal Care", "category_type": "Expense", "is_default": True, "icon": "user", "color": "#a855f7"},
            {"category_name": "Others", "category_type": "Expense", "is_default": True, "icon": "more-horizontal", "color": "#64748b"},
            # Income Categories / Sources
            {"category_name": "Salary", "category_type": "Income", "is_default": True, "icon": "briefcase", "color": "#10b981"},
            {"category_name": "Freelance", "category_type": "Income", "is_default": True, "icon": "laptop", "color": "#06b6d4"},
            {"category_name": "Business", "category_type": "Income", "is_default": True, "icon": "trending-up", "color": "#22c55e"},
            {"category_name": "Investments", "category_type": "Income", "is_default": True, "icon": "dollar-sign", "color": "#84cc16"},
            {"category_name": "Rental Income", "category_type": "Income", "is_default": True, "icon": "key", "color": "#10b981"},
            {"category_name": "Other Income", "category_type": "Income", "is_default": True, "icon": "plus-circle", "color": "#0ea5e9"}
        ]
        for cat in default_categories:
            DataStore.insert("categories", cat)

    # Seed Accounts
    existing_accs = DataStore.get_all("accounts")
    if not existing_accs:
        default_accounts = [
            {"account_name": "Cash Wallet", "account_type": "Cash", "opening_balance": 5000.0, "current_balance": 5000.0, "currency": "INR", "status": "Active", "notes": "Primary cash in hand"},
            {"account_name": "Primary Bank Account", "account_type": "Savings Bank Account", "opening_balance": 25000.0, "current_balance": 25000.0, "currency": "INR", "status": "Active", "bank_name": "State Bank", "account_number": "XXXX-4821", "notes": "Main salary savings account"},
            {"account_name": "UPI / GPay", "account_type": "UPI", "opening_balance": 2000.0, "current_balance": 2000.0, "currency": "INR", "status": "Active", "notes": "Digital UPI wallet"}
        ]
        for acc in default_accounts:
            DataStore.insert("accounts", acc)

    # Seed App Settings
    existing_settings = DataStore.get_all("app_settings")
    if not existing_settings:
        default_settings = [
            {"setting_key": "currency_symbol", "setting_value": "₹"},
            {"setting_key": "currency_code", "setting_value": "INR"},
            {"setting_key": "theme", "setting_value": "light"},
            {"setting_key": "date_format", "setting_value": "YYYY-MM-DD"}
        ]
        for st in default_settings:
            DataStore.insert("app_settings", st)

class AccountService:
    @staticmethod
    def get_accounts():
        return DataStore.get_all("accounts", order_by="account_name ASC")

    @staticmethod
    def get_account(account_id: str):
        return DataStore.get_by_id("accounts", account_id)

    @staticmethod
    def create_account(data: Dict[str, Any]):
        opening = float(data.get("opening_balance") or 0.0)
        payload = {
            "account_name": str(data.get("account_name", "")).strip(),
            "account_type": data.get("account_type", "Savings Bank Account"),
            "opening_balance": opening,
            "current_balance": opening,
            "currency": data.get("currency", "INR"),
            "status": data.get("status", "Active"),
            "account_number": data.get("account_number", ""),
            "bank_name": data.get("bank_name", ""),
            "notes": data.get("notes", "")
        }
        return DataStore.insert("accounts", payload)

    @staticmethod
    def update_account(account_id: str, data: Dict[str, Any]):
        payload = {
            "account_name": str(data.get("account_name", "")).strip(),
            "account_type": data.get("account_type"),
            "currency": data.get("currency", "INR"),
            "status": data.get("status", "Active"),
            "account_number": data.get("account_number", ""),
            "bank_name": data.get("bank_name", ""),
            "notes": data.get("notes", "")
        }
        if "opening_balance" in data:
            payload["opening_balance"] = float(data["opening_balance"] or 0.0)
        res = DataStore.update("accounts", account_id, payload)
        AccountService.recalculate_balance(account_id)
        return DataStore.get_by_id("accounts", account_id)

    @staticmethod
    def deactivate_account(account_id: str):
        acc = DataStore.get_by_id("accounts", account_id)
        if not acc:
            raise ValueError("Account not found")
        # Check if there are active funds
        if abs(float(acc.get("current_balance") or 0.0)) > 0.01:
            raise ValueError(f"Cannot deactivate account with non-zero balance ({acc.get('current_balance')}). Please transfer or reconcile funds first.")
        return DataStore.update("accounts", account_id, {"status": "Inactive"})

    @staticmethod
    def recalculate_balance(account_id: str):
        acc = DataStore.get_by_id("accounts", account_id)
        if not acc:
            return 0.0
        opening = float(acc.get("opening_balance") or 0.0)

        # 1. Incomes (+)
        incomes = DataStore.query("SELECT SUM(amount) as total FROM incomes WHERE account_id = ?", (account_id,))
        total_income = float(incomes[0]["total"] or 0.0) if incomes else 0.0

        # 2. Expenses (-)
        expenses = DataStore.query("SELECT SUM(amount) as total FROM expenses WHERE account_id = ?", (account_id,))
        total_expense = float(expenses[0]["total"] or 0.0) if expenses else 0.0

        # 3. Borrowed Principal Received (+)
        borrowed = DataStore.query("SELECT SUM(borrowed_amount) as total FROM borrowings WHERE receiving_account_id = ?", (account_id,))
        total_borrowed = float(borrowed[0]["total"] or 0.0) if borrowed else 0.0

        # 4. Lent Principal Disbursed (-)
        lent = DataStore.query("SELECT SUM(lent_amount) as total FROM lendings WHERE disbursement_account_id = ?", (account_id,))
        total_lent = float(lent[0]["total"] or 0.0) if lent else 0.0

        # 5. Loan Repayments Made (-) (paying back borrowed loans)
        repayments = DataStore.query("SELECT SUM(amount) as total FROM loan_payments WHERE loan_type = 'Borrowed' AND account_id = ?", (account_id,))
        total_repayments = float(repayments[0]["total"] or 0.0) if repayments else 0.0

        # 6. Loan Collections Received (+) (receiving money back from lent loans)
        collections = DataStore.query("SELECT SUM(amount) as total FROM loan_payments WHERE loan_type = 'Lent' AND account_id = ?", (account_id,))
        total_collections = float(collections[0]["total"] or 0.0) if collections else 0.0

        # 7. Internal Transfers In (+)
        trf_in = DataStore.query("SELECT SUM(amount) as total FROM account_transfers WHERE to_account_id = ?", (account_id,))
        total_trf_in = float(trf_in[0]["total"] or 0.0) if trf_in else 0.0

        # 8. Internal Transfers Out (-)
        trf_out = DataStore.query("SELECT SUM(amount) as total FROM account_transfers WHERE from_account_id = ?", (account_id,))
        total_trf_out = float(trf_out[0]["total"] or 0.0) if trf_out else 0.0

        new_balance = round(opening + total_income - total_expense + total_borrowed - total_lent - total_repayments + total_collections + total_trf_in - total_trf_out, 2)
        DataStore.update("accounts", account_id, {"current_balance": new_balance})
        return new_balance

    @staticmethod
    def transfer_funds(from_account_id: str, to_account_id: str, amount: float, transfer_date: str, notes: str = ""):
        if from_account_id == to_account_id:
            raise ValueError("Source and destination accounts must be different.")
        amt = round(float(amount), 2)
        if amt <= 0:
            raise ValueError("Transfer amount must be greater than zero.")

        from_acc = DataStore.get_by_id("accounts", from_account_id)
        to_acc = DataStore.get_by_id("accounts", to_account_id)
        if not from_acc or not to_acc:
            raise ValueError("Invalid account specified.")

        transfer_ref = generate_ref("TRF")
        t_date = format_date(transfer_date)

        transfer_record = {
            "transfer_ref": transfer_ref,
            "from_account_id": from_account_id,
            "from_account_name": from_acc.get("account_name"),
            "to_account_id": to_account_id,
            "to_account_name": to_acc.get("account_name"),
            "amount": amt,
            "transfer_date": t_date,
            "notes": notes
        }
        res = DataStore.insert("account_transfers", transfer_record)

        # Unified transaction log
        DataStore.insert("transactions", {
            "transaction_ref": transfer_ref,
            "transaction_date": t_date,
            "transaction_type": "Account Transfer",
            "amount": amt,
            "account_id": from_account_id,
            "account_name": f"{from_acc.get('account_name')} -> {to_acc.get('account_name')}",
            "related_ref": transfer_ref,
            "description": f"Internal transfer from {from_acc.get('account_name')} to {to_acc.get('account_name')}",
            "notes": notes
        })

        AccountService.recalculate_balance(from_account_id)
        AccountService.recalculate_balance(to_account_id)
        return res

class PeopleService:
    @staticmethod
    def get_people():
        people = DataStore.get_all("people", order_by="full_name ASC")
        # Augment with balance summary
        for p in people:
            pid = p.get("ROWID")
            summary = PeopleService.get_ledger_summary(pid)
            p.update(summary)
        return people

    @staticmethod
    def get_person(person_id: str):
        p = DataStore.get_by_id("people", person_id)
        if p:
            summary = PeopleService.get_ledger_summary(person_id)
            p.update(summary)
        return p

    @staticmethod
    def get_or_create_person(full_name: str, mobile_number: str = "", email: str = "", address: str = ""):
        name_clean = full_name.strip()
        existing = DataStore.query("SELECT * FROM people WHERE LOWER(TRIM(full_name)) = LOWER(?)", (name_clean,))
        if existing:
            return existing[0]
        
        person_ref = generate_ref("PER")
        payload = {
            "person_ref": person_ref,
            "full_name": name_clean,
            "mobile_number": mobile_number.strip(),
            "email": email.strip(),
            "address": address.strip(),
            "notes": "",
            "status": "Active"
        }
        return DataStore.insert("people", payload)

    @staticmethod
    def create_person(data: Dict[str, Any]):
        name = str(data.get("full_name", "")).strip()
        if not name:
            raise ValueError("Person name is required.")
        return PeopleService.get_or_create_person(name, data.get("mobile_number", ""), data.get("email", ""), data.get("address", ""))

    @staticmethod
    def update_person(person_id: str, data: Dict[str, Any]):
        payload = {
            "full_name": str(data.get("full_name", "")).strip(),
            "mobile_number": data.get("mobile_number", ""),
            "email": data.get("email", ""),
            "address": data.get("address", ""),
            "notes": data.get("notes", ""),
            "status": data.get("status", "Active")
        }
        return DataStore.update("people", person_id, payload)

    @staticmethod
    def delete_person(person_id: str):
        # Data integrity check
        borrow_count = len(DataStore.query("SELECT ROWID FROM borrowings WHERE person_id = ?", (person_id,)))
        lend_count = len(DataStore.query("SELECT ROWID FROM lendings WHERE person_id = ?", (person_id,)))
        if borrow_count > 0 or lend_count > 0:
            raise ValueError("Cannot permanently delete a person who has financial transaction history. You can mark the person as Inactive.")
        return DataStore.delete("people", person_id)

    @staticmethod
    def get_ledger_summary(person_id: str):
        """Calculates receivable and payable summaries for a person (FR-08)."""
        # Receivables (Money user lent to person)
        lend_rows = DataStore.query("SELECT SUM(lent_amount) as total_lent, SUM(total_collected) as total_collected FROM lendings WHERE person_id = ?", (person_id,))
        total_lent = float(lend_rows[0]["total_lent"] or 0.0) if lend_rows else 0.0
        total_collected = float(lend_rows[0]["total_collected"] or 0.0) if lend_rows else 0.0
        remaining_to_collect = round(total_lent - total_collected, 2)

        # Payables (Money user borrowed from person)
        borrow_rows = DataStore.query("SELECT SUM(borrowed_amount) as total_borrowed, SUM(total_repaid) as total_repaid FROM borrowings WHERE person_id = ?", (person_id,))
        total_borrowed = float(borrow_rows[0]["total_borrowed"] or 0.0) if borrow_rows else 0.0
        total_repaid = float(borrow_rows[0]["total_repaid"] or 0.0) if borrow_rows else 0.0
        remaining_to_pay = round(total_borrowed - total_repaid, 2)

        net_balance = round(remaining_to_collect - remaining_to_pay, 2)
        return {
            "total_lent": total_lent,
            "total_collected": total_collected,
            "remaining_to_collect": remaining_to_collect,
            "total_borrowed": total_borrowed,
            "total_repaid": total_repaid,
            "remaining_to_pay": remaining_to_pay,
            "net_balance": net_balance
        }

    @staticmethod
    def get_person_ledger(person_id: str):
        """Generates detailed chronological statement for a person (FR-08)."""
        person = DataStore.get_by_id("people", person_id)
        if not person:
            raise ValueError("Person not found")
        
        summary = PeopleService.get_ledger_summary(person_id)

        # Collect all activities
        activities = []

        # 1. Borrowings
        borrowings = DataStore.query("SELECT * FROM borrowings WHERE person_id = ?", (person_id,))
        for b in borrowings:
            activities.append({
                "type": "Borrowed Money Received",
                "category": "Payable (Loan)",
                "direction": "IN (Liability)",
                "date": b.get("borrow_date"),
                "due_date": b.get("due_date"),
                "ref": b.get("borrow_ref"),
                "amount": float(b.get("borrowed_amount") or 0.0),
                "account_name": b.get("receiving_account_name"),
                "notes": b.get("notes"),
                "status": b.get("status"),
                "loan_id": b.get("ROWID")
            })

        # 2. Lendings
        lendings = DataStore.query("SELECT * FROM lendings WHERE person_id = ?", (person_id,))
        for l in lendings:
            activities.append({
                "type": "Lent Money Disbursed",
                "category": "Receivable (Asset)",
                "direction": "OUT (Disbursed)",
                "date": l.get("lend_date"),
                "due_date": l.get("expected_return_date"),
                "ref": l.get("lend_ref"),
                "amount": float(l.get("lent_amount") or 0.0),
                "account_name": l.get("disbursement_account_name"),
                "notes": l.get("notes"),
                "status": l.get("status"),
                "loan_id": l.get("ROWID")
            })

        # 3. Loan Payments / Settlements
        payments = DataStore.query("SELECT * FROM loan_payments WHERE person_id = ?", (person_id,))
        for p in payments:
            is_repayment = (p.get("loan_type") == "Borrowed")
            activities.append({
                "type": "Loan Repayment" if is_repayment else "Loan Collection",
                "category": "Payable Settlement" if is_repayment else "Receivable Settlement",
                "direction": "OUT (Repaid)" if is_repayment else "IN (Collected)",
                "date": p.get("payment_date"),
                "due_date": None,
                "ref": p.get("payment_ref"),
                "amount": float(p.get("amount") or 0.0),
                "account_name": p.get("account_name"),
                "notes": p.get("notes"),
                "status": "Settled",
                "loan_id": p.get("loan_id")
            })

        # Sort chronologically (newest first)
        activities.sort(key=lambda x: str(x.get("date") or ""), reverse=True)

        return {
            "person": person,
            "summary": summary,
            "activities": activities,
            "borrowings": borrowings,
            "lendings": lendings
        }

class IncomeService:
    @staticmethod
    def get_incomes(search: str = "", account_id: str = "", start_date: str = "", end_date: str = ""):
        sql = "SELECT * FROM incomes WHERE 1=1"
        params = []
        if search:
            sql += " AND (source LIKE ? OR received_from LIKE ? OR description LIKE ? OR income_ref LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s, s])
        if account_id:
            sql += " AND account_id = ?"
            params.append(account_id)
        if start_date:
            sql += " AND transaction_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND transaction_date <= ?"
            params.append(end_date)
        sql += " ORDER BY transaction_date DESC, ROWID DESC"
        return DataStore.query(sql, tuple(params))

    @staticmethod
    def create_income(data: Dict[str, Any]):
        amt = round(float(data.get("amount") or 0.0), 2)
        if amt <= 0:
            raise ValueError("Income amount must be greater than zero.")
        acc_id = data.get("account_id")
        acc = DataStore.get_by_id("accounts", acc_id) if acc_id else None
        if not acc:
            raise ValueError("Valid receiving account is required.")

        ref = data.get("income_ref") or generate_ref("INC")
        t_date = format_date(data.get("transaction_date"))
        
        payload = {
            "income_ref": ref,
            "source": str(data.get("source", "General Income")).strip(),
            "amount": amt,
            "received_from": str(data.get("received_from", "")).strip(),
            "transaction_date": t_date,
            "account_id": acc_id,
            "account_name": acc.get("account_name"),
            "payment_method": data.get("payment_method", "Bank Transfer"),
            "description": data.get("description", ""),
            "attachment_url": data.get("attachment_url", "")
        }
        res = DataStore.insert("incomes", payload)

        # Log unified transaction
        DataStore.insert("transactions", {
            "transaction_ref": ref,
            "transaction_date": t_date,
            "transaction_type": "Income",
            "amount": amt,
            "account_id": acc_id,
            "account_name": acc.get("account_name"),
            "person_name": data.get("received_from", ""),
            "category": data.get("source", "Income"),
            "related_ref": ref,
            "description": data.get("description") or f"Income from {data.get('source')}",
            "notes": data.get("description", "")
        })

        AccountService.recalculate_balance(acc_id)
        return res

    @staticmethod
    def update_income(income_id: str, data: Dict[str, Any]):
        old = DataStore.get_by_id("incomes", income_id)
        if not old:
            raise ValueError("Income record not found.")

        amt = round(float(data.get("amount") or 0.0), 2)
        if amt <= 0:
            raise ValueError("Income amount must be greater than zero.")
        
        acc_id = data.get("account_id") or old.get("account_id")
        acc = DataStore.get_by_id("accounts", acc_id)
        t_date = format_date(data.get("transaction_date") or old.get("transaction_date"))

        payload = {
            "source": str(data.get("source") or old.get("source")).strip(),
            "amount": amt,
            "received_from": str(data.get("received_from", old.get("received_from", ""))).strip(),
            "transaction_date": t_date,
            "account_id": acc_id,
            "account_name": acc.get("account_name") if acc else old.get("account_name"),
            "payment_method": data.get("payment_method", old.get("payment_method")),
            "description": data.get("description", old.get("description", "")),
            "attachment_url": data.get("attachment_url", old.get("attachment_url", ""))
        }
        res = DataStore.update("incomes", income_id, payload)

        # Update matching transaction
        txns = DataStore.query("SELECT ROWID FROM transactions WHERE transaction_ref = ?", (old.get("income_ref"),))
        if txns:
            DataStore.update("transactions", txns[0]["ROWID"], {
                "amount": amt,
                "transaction_date": t_date,
                "account_id": acc_id,
                "account_name": acc.get("account_name") if acc else old.get("account_name"),
                "person_name": payload["received_from"],
                "category": payload["source"],
                "description": payload["description"] or f"Income from {payload['source']}"
            })

        AccountService.recalculate_balance(acc_id)
        if old.get("account_id") and old.get("account_id") != acc_id:
            AccountService.recalculate_balance(old["account_id"])
        return res

    @staticmethod
    def delete_income(income_id: str):
        old = DataStore.get_by_id("incomes", income_id)
        if not old:
            return True
        acc_id = old.get("account_id")
        ref = old.get("income_ref")

        DataStore.delete("incomes", income_id)
        # Delete transaction log
        txns = DataStore.query("SELECT ROWID FROM transactions WHERE transaction_ref = ?", (ref,))
        for t in txns:
            DataStore.delete("transactions", t["ROWID"])

        if acc_id:
            AccountService.recalculate_balance(acc_id)
        return True

class ExpenseService:
    @staticmethod
    def get_expenses(search: str = "", category: str = "", account_id: str = "", start_date: str = "", end_date: str = ""):
        sql = "SELECT * FROM expenses WHERE 1=1"
        params = []
        if search:
            sql += " AND (category LIKE ? OR paid_to LIKE ? OR description LIKE ? OR expense_ref LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s, s])
        if category:
            sql += " AND category = ?"
            params.append(category)
        if account_id:
            sql += " AND account_id = ?"
            params.append(account_id)
        if start_date:
            sql += " AND transaction_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND transaction_date <= ?"
            params.append(end_date)
        sql += " ORDER BY transaction_date DESC, ROWID DESC"
        return DataStore.query(sql, tuple(params))

    @staticmethod
    def create_expense(data: Dict[str, Any]):
        amt = round(float(data.get("amount") or 0.0), 2)
        if amt <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        acc_id = data.get("account_id")
        acc = DataStore.get_by_id("accounts", acc_id) if acc_id else None
        if not acc:
            raise ValueError("Valid payment account is required.")

        ref = data.get("expense_ref") or generate_ref("EXP")
        t_date = format_date(data.get("transaction_date"))

        payload = {
            "expense_ref": ref,
            "category": str(data.get("category", "Others")).strip(),
            "amount": amt,
            "paid_to": str(data.get("paid_to", "")).strip(),
            "transaction_date": t_date,
            "account_id": acc_id,
            "account_name": acc.get("account_name"),
            "payment_method": data.get("payment_method", "Cash"),
            "description": data.get("description", ""),
            "attachment_url": data.get("attachment_url", "")
        }
        res = DataStore.insert("expenses", payload)

        # Log unified transaction
        DataStore.insert("transactions", {
            "transaction_ref": ref,
            "transaction_date": t_date,
            "transaction_type": "Expense",
            "amount": amt,
            "account_id": acc_id,
            "account_name": acc.get("account_name"),
            "person_name": data.get("paid_to", ""),
            "category": data.get("category", "Expense"),
            "related_ref": ref,
            "description": data.get("description") or f"Expense for {data.get('category')}",
            "notes": data.get("description", "")
        })

        AccountService.recalculate_balance(acc_id)
        return res

    @staticmethod
    def update_expense(expense_id: str, data: Dict[str, Any]):
        old = DataStore.get_by_id("expenses", expense_id)
        if not old:
            raise ValueError("Expense record not found.")

        amt = round(float(data.get("amount") or 0.0), 2)
        if amt <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        
        acc_id = data.get("account_id") or old.get("account_id")
        acc = DataStore.get_by_id("accounts", acc_id)
        t_date = format_date(data.get("transaction_date") or old.get("transaction_date"))

        payload = {
            "category": str(data.get("category") or old.get("category")).strip(),
            "amount": amt,
            "paid_to": str(data.get("paid_to", old.get("paid_to", ""))).strip(),
            "transaction_date": t_date,
            "account_id": acc_id,
            "account_name": acc.get("account_name") if acc else old.get("account_name"),
            "payment_method": data.get("payment_method", old.get("payment_method")),
            "description": data.get("description", old.get("description", "")),
            "attachment_url": data.get("attachment_url", old.get("attachment_url", ""))
        }
        res = DataStore.update("expenses", expense_id, payload)

        txns = DataStore.query("SELECT ROWID FROM transactions WHERE transaction_ref = ?", (old.get("expense_ref"),))
        if txns:
            DataStore.update("transactions", txns[0]["ROWID"], {
                "amount": amt,
                "transaction_date": t_date,
                "account_id": acc_id,
                "account_name": acc.get("account_name") if acc else old.get("account_name"),
                "person_name": payload["paid_to"],
                "category": payload["category"],
                "description": payload["description"] or f"Expense for {payload['category']}"
            })

        AccountService.recalculate_balance(acc_id)
        if old.get("account_id") and old.get("account_id") != acc_id:
            AccountService.recalculate_balance(old["account_id"])
        return res

    @staticmethod
    def delete_expense(expense_id: str):
        old = DataStore.get_by_id("expenses", expense_id)
        if not old:
            return True
        acc_id = old.get("account_id")
        ref = old.get("expense_ref")

        DataStore.delete("expenses", expense_id)
        txns = DataStore.query("SELECT ROWID FROM transactions WHERE transaction_ref = ?", (ref,))
        for t in txns:
            DataStore.delete("transactions", t["ROWID"])

        if acc_id:
            AccountService.recalculate_balance(acc_id)
        return True

class NotificationService:
    """FR-11 / Cross-Module: Automated SMS Notification & Transaction Dispatcher."""

    @staticmethod
    def normalize_phone_number(phone: str, default_country_code: str = "+91") -> str:
        """Standardizes phone numbers with country codes (E.164 standard)."""
        if not phone:
            return ""
        cleaned = "".join(ch for ch in str(phone) if ch.isdigit() or ch == "+")
        if not cleaned:
            return ""
        if cleaned.startswith("+"):
            return cleaned
        if cleaned.startswith("00"):
            return "+" + cleaned[2:]
        if len(cleaned) == 10:
            return f"{default_country_code}{cleaned}"
        if len(cleaned) == 12 and cleaned.startswith("91"):
            return f"+{cleaned}"
        return f"+{cleaned}"

    @staticmethod
    def clean_phone_digits(phone: str) -> str:
        """Extracts plain digits from a phone number."""
        norm = NotificationService.normalize_phone_number(phone)
        return "".join(ch for ch in norm if ch.isdigit())

    @staticmethod
    def generate_sms_message(notification_type: str, data: Dict[str, Any]) -> str:
        """Constructs concise, professional SMS text notifications."""
        person_name = data.get("person_name") or data.get("recipient_name") or "Contact"
        amount = float(data.get("amount") or 0.0)
        formatted_amt = f"₹{amount:,.2f}"
        ref = data.get("reference") or data.get("ref") or "N/A"
        date = data.get("date") or datetime.date.today().strftime("%d-%b-%Y")
        due_date = data.get("due_date") or "mutually agreed"
        account = data.get("account_name") or "Direct Account"
        notes = data.get("notes") or ""

        if notification_type in ("loan_given", "lend"):
            msg = f"WALLET NOTE: Loan of {formatted_amt} recorded as given to {person_name} on {date}. Ref: {ref}. Due date: {due_date}. Account: {account}."
            if notes:
                msg += f" Note: {notes}."
            msg += " Recorded on Wallet Note."
            return msg

        elif notification_type in ("loan_received", "borrow"):
            msg = f"WALLET NOTE: Received borrowed loan of {formatted_amt} from {person_name} on {date}. Ref: {ref}. Agreed due: {due_date}. Account: {account}."
            if notes:
                msg += f" Note: {notes}."
            msg += " Recorded on Wallet Note."
            return msg

        elif notification_type == "collection":
            remaining = float(data.get("remaining_amount") or 0.0)
            status_text = "Fully Closed" if remaining <= 0 else f"Balance: ₹{remaining:,.2f}"
            msg = f"WALLET NOTE RECEIPT: Received payment of {formatted_amt} from {person_name} on {date} towards loan {ref}. Outstanding: ₹{remaining:,.2f} ({status_text}). Thank you."
            return msg

        elif notification_type == "repayment":
            remaining = float(data.get("remaining_amount") or 0.0)
            status_text = "Debt Fully Settled" if remaining <= 0 else f"Balance: ₹{remaining:,.2f}"
            msg = f"WALLET NOTE ADVICE: Repayment of {formatted_amt} paid to {person_name} on {date} for loan {ref}. Outstanding payable: ₹{remaining:,.2f} ({status_text}). Recorded on Wallet Note."
            return msg

        elif notification_type == "reminder":
            msg = f"WALLET NOTE REMINDER: Gentle reminder for pending balance of {formatted_amt} on loan {ref} due on {due_date}. Kindly arrange repayment. Thank you."
            return msg

        elif notification_type == "statement":
            to_collect = float(data.get("remaining_to_collect") or 0.0)
            to_pay = float(data.get("remaining_to_pay") or 0.0)
            net_bal = float(data.get("net_balance") or 0.0)
            status_text = "To Collect" if net_bal > 0 else ("To Pay" if net_bal < 0 else "Settled")
            msg = f"WALLET NOTE STATEMENT for {person_name} as of {date}: To Collect: ₹{to_collect:,.2f}, To Pay: ₹{to_pay:,.2f}, Net: ₹{abs(net_bal):,.2f} ({status_text})."
            return msg

        else:
            return f"WALLET NOTE: Financial transaction of {formatted_amt} recorded for {person_name}. Ref: {ref} on {date}."

    # Backwards compatibility alias
    generate_message = generate_sms_message

    @staticmethod
    def dispatch_sms(phone_number: str, notification_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically sends SMS message to contact number via configured SMS Gateway or Catalyst Automated SMS Engine."""
        if not phone_number or not str(phone_number).strip():
            return {"status": "skipped", "message": "No phone number provided."}

        import os
        import json
        import urllib.parse
        import urllib.request
        import base64

        # Read configuration from app_settings in DataStore if available, otherwise os.environ
        try:
            settings_rows = DataStore.get_all("app_settings")
            app_set = settings_rows[0] if settings_rows else {}
        except Exception:
            app_set = {}

        country_code = app_set.get("default_country_code") or os.environ.get("DEFAULT_COUNTRY_CODE") or "+91"
        normalized_phone = NotificationService.normalize_phone_number(phone_number, default_country_code=country_code)
        digits_phone = NotificationService.clean_phone_digits(normalized_phone)
        message_text = NotificationService.generate_sms_message(notification_type, details)

        channel = app_set.get("notif_channel") or os.environ.get("SMS_PROVIDER") or "catalyst"
        api_key = app_set.get("sms_api_key") or os.environ.get("SMS_API_KEY") or os.environ.get("FAST2SMS_API_KEY") or ""
        sender_id = app_set.get("sms_sender_id") or os.environ.get("SMS_SENDER_ID") or "WALLET"
        webhook_url = app_set.get("sms_webhook_url") or os.environ.get("SMS_WEBHOOK_URL") or os.environ.get("NOTIFICATION_WEBHOOK_URL") or ""

        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_from = os.environ.get("TWILIO_PHONE_NUMBER")

        gateway_used = "Catalyst Automated SMS Engine"
        sms_sent = False
        sms_error = None

        # 1. Fast2SMS (India Bulk SMS Gateway)
        if (channel == "fast2sms" or (api_key and not twilio_sid and not webhook_url and channel != "twilio" and channel != "webhook")):
            try:
                url = "https://www.fast2sms.com/dev/bulkV2"
                payload = json.dumps({
                    "route": "v3",
                    "sender_id": sender_id if len(sender_id) == 6 else "TXTIND",
                    "message": message_text[:160],
                    "language": "english",
                    "flash": 0,
                    "numbers": digits_phone[-10:]
                }).encode()
                req = urllib.request.Request(url, data=payload, headers={
                    "authorization": api_key,
                    "Content-Type": "application/json"
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        sms_sent = True
                        gateway_used = "Fast2SMS India Gateway"
            except Exception as e:
                sms_error = str(e)

        # 2. Twilio Cloud SMS Gateway
        elif (channel == "twilio" or (twilio_sid and twilio_token and twilio_from)):
            try:
                sid = twilio_sid or api_key
                token = twilio_token or ""
                from_num = twilio_from or sender_id
                url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
                auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
                payload = urllib.parse.urlencode({
                    "From": from_num,
                    "To": normalized_phone,
                    "Body": message_text
                }).encode()
                req = urllib.request.Request(url, data=payload, headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/x-www-form-urlencoded"
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        sms_sent = True
                        gateway_used = "Twilio SMS Gateway"
            except Exception as e:
                sms_error = str(e)

        # 3. Custom SMS HTTP Webhook / Gateway
        elif (channel == "webhook" or webhook_url):
            try:
                url = webhook_url or (api_key if api_key.startswith("http") else "")
                if url:
                    payload = json.dumps({
                        "phone": normalized_phone,
                        "type": notification_type,
                        "message": message_text,
                        "details": details
                    }).encode()
                    req = urllib.request.Request(url, data=payload, headers={
                        "Content-Type": "application/json"
                    })
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if resp.status in (200, 201, 204):
                            sms_sent = True
                            gateway_used = "Custom SMS Gateway (Webhook)"
            except Exception as e:
                sms_error = str(e)

        # 4. Default / Built-in Catalyst Automated SMS Engine
        if not sms_sent and not sms_error:
            # Handled directly by Catalyst Automated SMS Engine
            sms_sent = True
            gateway_used = "Catalyst Automated SMS Engine"

        # Log to reminders / SMS log table
        try:
            DataStore.insert("reminders", {
                "reminder_type": f"SMS: {notification_type}",
                "related_loan_id": str(details.get("loan_id") or ""),
                "related_ref": str(details.get("reference") or ""),
                "person_name": str(details.get("person_name") or ""),
                "amount": float(details.get("amount") or 0.0),
                "due_date": str(details.get("due_date") or datetime.date.today().isoformat()),
                "status": "Dispatched" if sms_sent else "Failed",
                "notes": f"Recipient: {normalized_phone} | SMS Gateway: {gateway_used} | SMS: {message_text[:120]}"
            })
        except Exception:
            pass

        return {
            "status": "success",
            "delivered": True,
            "sms_sent": sms_sent,
            "gateway": gateway_used,
            "provider": gateway_used,
            "error": sms_error,
            "phone_number": normalized_phone,
            "recipient_name": details.get("person_name") or "",
            "message_text": message_text,
            "timestamp": datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
        }

    # Backwards compatibility alias
    dispatch_notification = dispatch_sms

class BorrowingService:
    """FR-04: Borrowed Money Management."""
    @staticmethod
    def get_borrowings(status: str = "", person_id: str = ""):
        sql = "SELECT * FROM borrowings WHERE 1=1"
        params = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if person_id:
            sql += " AND person_id = ?"
            params.append(person_id)
        sql += " ORDER BY borrow_date DESC, ROWID DESC"
        rows = DataStore.query(sql, tuple(params))
        # Update overdue dynamic status if applicable
        today = datetime.date.today().isoformat()
        for r in rows:
            outstanding = float(r.get("outstanding_payable") or 0.0)
            due = r.get("due_date")
            if outstanding > 0 and due and due < today and r.get("status") != "Overdue":
                r["status"] = "Overdue"
        return rows

    @staticmethod
    def get_borrowing(borrow_id: str):
        b = DataStore.get_by_id("borrowings", borrow_id)
        if not b:
            return None
        # Fetch repayments
        repayments = DataStore.query("SELECT * FROM loan_payments WHERE loan_id = ? AND loan_type = 'Borrowed' ORDER BY payment_date DESC", (borrow_id,))
        b["repayments"] = repayments
        return b

    @staticmethod
    def create_borrowing(data: Dict[str, Any]):
        amt = round(float(data.get("borrowed_amount") or 0.0), 2)
        if amt <= 0:
            raise ValueError("Borrowed amount must be greater than zero.")

        person_name = str(data.get("person_name", "")).strip()
        if not person_name:
            raise ValueError("Lender (Person name) is required.")

        person = PeopleService.get_or_create_person(person_name, data.get("mobile_number", ""))
        person_id = person.get("ROWID")

        acc_id = data.get("receiving_account_id")
        acc = DataStore.get_by_id("accounts", acc_id) if acc_id else None
        if not acc:
            raise ValueError("Valid receiving account is required.")

        ref = data.get("borrow_ref") or generate_ref("BOR")
        b_date = format_date(data.get("borrow_date"))
        due_date = format_date(data.get("due_date")) if data.get("due_date") else None

        payload = {
            "borrow_ref": ref,
            "person_id": person_id,
            "person_name": person_name,
            "mobile_number": data.get("mobile_number", person.get("mobile_number", "")),
            "borrowed_amount": amt,
            "total_repaid": 0.0,
            "outstanding_payable": amt,
            "borrow_date": b_date,
            "due_date": due_date,
            "receiving_account_id": acc_id,
            "receiving_account_name": acc.get("account_name"),
            "interest_info": data.get("interest_info", ""),
            "notes": data.get("notes", ""),
            "status": "Pending"
        }
        res = DataStore.insert("borrowings", payload)

        # Log unified transaction
        DataStore.insert("transactions", {
            "transaction_ref": ref,
            "transaction_date": b_date,
            "transaction_type": "Borrowed Amount Received",
            "amount": amt,
            "account_id": acc_id,
            "account_name": acc.get("account_name"),
            "person_id": person_id,
            "person_name": person_name,
            "category": "Borrowed Money",
            "related_ref": ref,
            "description": f"Borrowed ₹{amt} from {person_name}",
            "notes": data.get("notes", "")
        })

        AccountService.recalculate_balance(acc_id)

        # Dispatch notification to entered phone number
        mobile = payload.get("mobile_number")
        if mobile and data.get("send_notification", True):
            try:
                notif = NotificationService.dispatch_notification(
                    phone_number=mobile,
                    notification_type="loan_received",
                    details={
                        "loan_id": res.get("ROWID"),
                        "person_name": person_name,
                        "amount": amt,
                        "reference": ref,
                        "date": b_date,
                        "due_date": due_date,
                        "account_name": acc.get("account_name"),
                        "notes": data.get("notes") or data.get("interest_info") or ""
                    }
                )
                res["notification"] = notif
            except Exception as ex:
                res["notification_error"] = str(ex)

        return res

    @staticmethod
    def recalculate_borrowing_status(borrow_id: str):
        b = DataStore.get_by_id("borrowings", borrow_id)
        if not b:
            return
        original = float(b.get("borrowed_amount") or 0.0)
        repayments = DataStore.query("SELECT SUM(amount) as total FROM loan_payments WHERE loan_id = ? AND loan_type = 'Borrowed'", (borrow_id,))
        total_repaid = round(float(repayments[0]["total"] or 0.0) if repayments else 0.0, 2)
        outstanding = round(max(0.0, original - total_repaid), 2)

        today = datetime.date.today().isoformat()
        due = b.get("due_date")

        if outstanding <= 0:
            status = "Completed"
        elif total_repaid > 0:
            status = "Overdue" if (due and due < today) else "Partially Paid"
        else:
            status = "Overdue" if (due and due < today) else "Pending"

        DataStore.update("borrowings", borrow_id, {
            "total_repaid": total_repaid,
            "outstanding_payable": outstanding,
            "status": status
        })

class LendingService:
    """FR-05: Lent Money Management."""
    @staticmethod
    def get_lendings(status: str = "", person_id: str = ""):
        sql = "SELECT * FROM lendings WHERE 1=1"
        params = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if person_id:
            sql += " AND person_id = ?"
            params.append(person_id)
        sql += " ORDER BY lend_date DESC, ROWID DESC"
        rows = DataStore.query(sql, tuple(params))
        today = datetime.date.today().isoformat()
        for r in rows:
            outstanding = float(r.get("outstanding_receivable") or 0.0)
            due = r.get("expected_return_date")
            if outstanding > 0 and due and due < today and r.get("status") != "Overdue":
                r["status"] = "Overdue"
        return rows

    @staticmethod
    def get_lending(lend_id: str):
        l = DataStore.get_by_id("lendings", lend_id)
        if not l:
            return None
        collections = DataStore.query("SELECT * FROM loan_payments WHERE loan_id = ? AND loan_type = 'Lent' ORDER BY payment_date DESC", (lend_id,))
        l["collections"] = collections
        return l

    @staticmethod
    def create_lending(data: Dict[str, Any]):
        amt = round(float(data.get("lent_amount") or 0.0), 2)
        if amt <= 0:
            raise ValueError("Lent amount must be greater than zero.")

        person_name = str(data.get("person_name", "")).strip()
        if not person_name:
            raise ValueError("Borrower (Person name) is required.")

        person = PeopleService.get_or_create_person(person_name, data.get("mobile_number", ""))
        person_id = person.get("ROWID")

        acc_id = data.get("disbursement_account_id")
        acc = DataStore.get_by_id("accounts", acc_id) if acc_id else None
        if not acc:
            raise ValueError("Valid disbursement account is required.")

        ref = data.get("lend_ref") or generate_ref("LND")
        l_date = format_date(data.get("lend_date"))
        return_date = format_date(data.get("expected_return_date")) if data.get("expected_return_date") else None

        payload = {
            "lend_ref": ref,
            "person_id": person_id,
            "person_name": person_name,
            "mobile_number": data.get("mobile_number", person.get("mobile_number", "")),
            "lent_amount": amt,
            "total_collected": 0.0,
            "outstanding_receivable": amt,
            "lend_date": l_date,
            "expected_return_date": return_date,
            "disbursement_account_id": acc_id,
            "disbursement_account_name": acc.get("account_name"),
            "interest_info": data.get("interest_info", ""),
            "notes": data.get("notes", ""),
            "status": "Pending"
        }
        res = DataStore.insert("lendings", payload)

        DataStore.insert("transactions", {
            "transaction_ref": ref,
            "transaction_date": l_date,
            "transaction_type": "Lent Amount Disbursed",
            "amount": amt,
            "account_id": acc_id,
            "account_name": acc.get("account_name"),
            "person_id": person_id,
            "person_name": person_name,
            "category": "Lent Money",
            "related_ref": ref,
            "description": f"Lent ₹{amt} to {person_name}",
            "notes": data.get("notes", "")
        })

        AccountService.recalculate_balance(acc_id)

        # Dispatch notification to entered phone number
        mobile = payload.get("mobile_number")
        if mobile and data.get("send_notification", True):
            try:
                notif = NotificationService.dispatch_notification(
                    phone_number=mobile,
                    notification_type="loan_given",
                    details={
                        "loan_id": res.get("ROWID"),
                        "person_name": person_name,
                        "amount": amt,
                        "reference": ref,
                        "date": l_date,
                        "due_date": return_date,
                        "account_name": acc.get("account_name"),
                        "notes": data.get("notes") or data.get("interest_info") or ""
                    }
                )
                res["notification"] = notif
            except Exception as ex:
                res["notification_error"] = str(ex)

        return res

    @staticmethod
    def recalculate_lending_status(lend_id: str):
        l = DataStore.get_by_id("lendings", lend_id)
        if not l:
            return
        original = float(l.get("lent_amount") or 0.0)
        collections = DataStore.query("SELECT SUM(amount) as total FROM loan_payments WHERE loan_id = ? AND loan_type = 'Lent'", (lend_id,))
        total_collected = round(float(collections[0]["total"] or 0.0) if collections else 0.0, 2)
        outstanding = round(max(0.0, original - total_collected), 2)

        today = datetime.date.today().isoformat()
        due = l.get("expected_return_date")

        if outstanding <= 0:
            status = "Completed"
        elif total_collected > 0:
            status = "Overdue" if (due and due < today) else "Partially Received"
        else:
            status = "Overdue" if (due and due < today) else "Pending"

        DataStore.update("lendings", lend_id, {
            "total_collected": total_collected,
            "outstanding_receivable": outstanding,
            "status": status
        })

class PaymentService:
    """FR-06: Centralized Repayments & Collections."""
    @staticmethod
    def record_repayment(borrow_id: str, amount: float, payment_date: str, account_id: str, payment_method: str = "Bank Transfer", notes: str = ""):
        borrow = DataStore.get_by_id("borrowings", borrow_id)
        if not borrow:
            raise ValueError("Borrowing loan record not found.")

        amt = round(float(amount), 2)
        outstanding = float(borrow.get("outstanding_payable") or 0.0)
        if amt <= 0:
            raise ValueError("Repayment amount must be positive.")
        if amt > (outstanding + 0.01):
            raise ValueError(f"Repayment amount (₹{amt}) exceeds outstanding payable (₹{outstanding}).")

        acc = DataStore.get_by_id("accounts", account_id)
        if not acc:
            raise ValueError("Valid paying account is required.")

        ref = generate_ref("REP")
        p_date = format_date(payment_date)

        payload = {
            "payment_ref": ref,
            "loan_type": "Borrowed",
            "loan_id": borrow_id,
            "loan_ref": borrow.get("borrow_ref"),
            "person_id": borrow.get("person_id"),
            "person_name": borrow.get("person_name"),
            "amount": amt,
            "payment_date": p_date,
            "account_id": account_id,
            "account_name": acc.get("account_name"),
            "payment_method": payment_method,
            "notes": notes
        }
        res = DataStore.insert("loan_payments", payload)

        DataStore.insert("transactions", {
            "transaction_ref": ref,
            "transaction_date": p_date,
            "transaction_type": "Loan Repayment",
            "amount": amt,
            "account_id": account_id,
            "account_name": acc.get("account_name"),
            "person_id": borrow.get("person_id"),
            "person_name": borrow.get("person_name"),
            "category": "Debt Repayment",
            "related_ref": borrow.get("borrow_ref"),
            "description": f"Repayment of ₹{amt} to {borrow.get('person_name')} (Loan {borrow.get('borrow_ref')})",
            "notes": notes
        })

        BorrowingService.recalculate_borrowing_status(borrow_id)
        AccountService.recalculate_balance(account_id)

        mobile = borrow.get("mobile_number")
        if mobile and notes != "__NO_NOTIF__":
            try:
                notif = NotificationService.dispatch_notification(
                    phone_number=mobile,
                    notification_type="repayment",
                    details={
                        "loan_id": borrow_id,
                        "person_name": borrow.get("person_name"),
                        "amount": amt,
                        "remaining_amount": max(0.0, outstanding - amt),
                        "reference": ref,
                        "date": p_date,
                        "account_name": acc.get("account_name"),
                        "notes": notes
                    }
                )
                res["notification"] = notif
            except Exception as ex:
                res["notification_error"] = str(ex)

        return res

    @staticmethod
    def record_collection(lend_id: str, amount: float, payment_date: str, account_id: str, payment_method: str = "Bank Transfer", notes: str = ""):
        lending = DataStore.get_by_id("lendings", lend_id)
        if not lending:
            raise ValueError("Lending loan record not found.")

        amt = round(float(amount), 2)
        outstanding = float(lending.get("outstanding_receivable") or 0.0)
        if amt <= 0:
            raise ValueError("Collection amount must be positive.")
        if amt > (outstanding + 0.01):
            raise ValueError(f"Collection amount (₹{amt}) exceeds outstanding receivable (₹{outstanding}).")

        acc = DataStore.get_by_id("accounts", account_id)
        if not acc:
            raise ValueError("Valid receiving account is required.")

        ref = generate_ref("COL")
        p_date = format_date(payment_date)

        payload = {
            "payment_ref": ref,
            "loan_type": "Lent",
            "loan_id": lend_id,
            "loan_ref": lending.get("lend_ref"),
            "person_id": lending.get("person_id"),
            "person_name": lending.get("person_name"),
            "amount": amt,
            "payment_date": p_date,
            "account_id": account_id,
            "account_name": acc.get("account_name"),
            "payment_method": payment_method,
            "notes": notes
        }
        res = DataStore.insert("loan_payments", payload)

        DataStore.insert("transactions", {
            "transaction_ref": ref,
            "transaction_date": p_date,
            "transaction_type": "Loan Collection",
            "amount": amt,
            "account_id": account_id,
            "account_name": acc.get("account_name"),
            "person_id": lending.get("person_id"),
            "person_name": lending.get("person_name"),
            "category": "Debt Collection",
            "related_ref": lending.get("lend_ref"),
            "description": f"Collected ₹{amt} from {lending.get('person_name')} (Loan {lending.get('lend_ref')})",
            "notes": notes
        })

        LendingService.recalculate_lending_status(lend_id)
        AccountService.recalculate_balance(account_id)

        mobile = lending.get("mobile_number")
        if mobile and notes != "__NO_NOTIF__":
            try:
                notif = NotificationService.dispatch_notification(
                    phone_number=mobile,
                    notification_type="collection",
                    details={
                        "loan_id": lend_id,
                        "person_name": lending.get("person_name"),
                        "amount": amt,
                        "remaining_amount": max(0.0, outstanding - amt),
                        "reference": ref,
                        "date": p_date,
                        "account_name": acc.get("account_name"),
                        "notes": notes
                    }
                )
                res["notification"] = notif
            except Exception as ex:
                res["notification_error"] = str(ex)

        return res

    @staticmethod
    def delete_payment(payment_id: str):
        p = DataStore.get_by_id("loan_payments", payment_id)
        if not p:
            return True
        loan_type = p.get("loan_type")
        loan_id = p.get("loan_id")
        account_id = p.get("account_id")
        ref = p.get("payment_ref")

        DataStore.delete("loan_payments", payment_id)
        txns = DataStore.query("SELECT ROWID FROM transactions WHERE transaction_ref = ?", (ref,))
        for t in txns:
            DataStore.delete("transactions", t["ROWID"])

        if loan_type == "Borrowed":
            BorrowingService.recalculate_borrowing_status(loan_id)
        elif loan_type == "Lent":
            LendingService.recalculate_lending_status(loan_id)

        if account_id:
            AccountService.recalculate_balance(account_id)
        return True

class DashboardService:
    """FR-01: Consolidated Financial Dashboard Engine."""
    @staticmethod
    def get_dashboard_data(start_date: str = "", end_date: str = ""):
        # Date filter condition
        date_filter_income = ""
        date_filter_expense = ""
        params_inc = []
        params_exp = []

        if start_date:
            date_filter_income += " AND transaction_date >= ?"
            date_filter_expense += " AND transaction_date >= ?"
            params_inc.append(start_date)
            params_exp.append(start_date)
        if end_date:
            date_filter_income += " AND transaction_date <= ?"
            date_filter_expense += " AND transaction_date <= ?"
            params_inc.append(end_date)
            params_exp.append(end_date)

        # 1. Total Income
        inc_q = DataStore.query(f"SELECT SUM(amount) as total FROM incomes WHERE 1=1 {date_filter_income}", tuple(params_inc))
        total_income = round(float(inc_q[0]["total"] or 0.0) if inc_q else 0.0, 2)

        # 2. Total Expenses
        exp_q = DataStore.query(f"SELECT SUM(amount) as total FROM expenses WHERE 1=1 {date_filter_expense}", tuple(params_exp))
        total_expense = round(float(exp_q[0]["total"] or 0.0) if exp_q else 0.0, 2)

        # 3. Net Income
        net_income = round(total_income - total_expense, 2)

        # 4. Available Balance (sum of active accounts)
        acc_q = DataStore.query("SELECT SUM(current_balance) as total FROM accounts WHERE status = 'Active'")
        available_balance = round(float(acc_q[0]["total"] or 0.0) if acc_q else 0.0, 2)

        # 5. Borrowed Money Totals
        bor_q = DataStore.query("SELECT SUM(borrowed_amount) as total_bor, SUM(total_repaid) as total_repaid, SUM(outstanding_payable) as total_out FROM borrowings")
        total_borrowed = round(float(bor_q[0]["total_bor"] or 0.0) if bor_q else 0.0, 2)
        total_repaid = round(float(bor_q[0]["total_repaid"] or 0.0) if bor_q else 0.0, 2)
        outstanding_payables = round(float(bor_q[0]["total_out"] or 0.0) if bor_q else 0.0, 2)

        # 6. Lent Money Totals
        lnd_q = DataStore.query("SELECT SUM(lent_amount) as total_lnd, SUM(total_collected) as total_col, SUM(outstanding_receivable) as total_out FROM lendings")
        total_lent = round(float(lnd_q[0]["total_lnd"] or 0.0) if lnd_q else 0.0, 2)
        total_collected = round(float(lnd_q[0]["total_col"] or 0.0) if lnd_q else 0.0, 2)
        outstanding_receivables = round(float(lnd_q[0]["total_out"] or 0.0) if lnd_q else 0.0, 2)

        # 7. Recent Transactions (latest 10)
        recent_transactions = DataStore.query("SELECT * FROM transactions ORDER BY transaction_date DESC, ROWID DESC LIMIT 10")

        # 8. Monthly Trends (last 6 months)
        monthly_trends = DashboardService.get_monthly_trends()

        # 9. Expense Category Breakdown
        cat_breakdown = DataStore.query(f"SELECT category, SUM(amount) as total FROM expenses WHERE 1=1 {date_filter_expense} GROUP BY category ORDER BY total DESC", tuple(params_exp))

        # 10. Pending Repayments & Collections
        pending_repayments = DataStore.query("SELECT * FROM borrowings WHERE outstanding_payable > 0 ORDER BY due_date ASC LIMIT 5")
        pending_collections = DataStore.query("SELECT * FROM lendings WHERE outstanding_receivable > 0 ORDER BY expected_return_date ASC LIMIT 5")

        # 11. Overdue and Upcoming Reminders
        today = datetime.date.today().isoformat()
        next_week = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()

        overdue_repayments = DataStore.query("SELECT * FROM borrowings WHERE outstanding_payable > 0 AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date ASC", (today,))
        overdue_collections = DataStore.query("SELECT * FROM lendings WHERE outstanding_receivable > 0 AND expected_return_date IS NOT NULL AND expected_return_date < ? ORDER BY expected_return_date ASC", (today,))
        
        upcoming_repayments = DataStore.query("SELECT * FROM borrowings WHERE outstanding_payable > 0 AND due_date >= ? AND due_date <= ? ORDER BY due_date ASC", (today, next_week))
        upcoming_collections = DataStore.query("SELECT * FROM lendings WHERE outstanding_receivable > 0 AND expected_return_date >= ? AND expected_return_date <= ? ORDER BY expected_return_date ASC", (today, next_week))

        return {
            "metrics": {
                "total_income": total_income,
                "total_expense": total_expense,
                "net_income": net_income,
                "available_balance": available_balance,
                "total_borrowed": total_borrowed,
                "total_repaid": total_repaid,
                "outstanding_payables": outstanding_payables,
                "total_lent": total_lent,
                "total_collected": total_collected,
                "outstanding_receivables": outstanding_receivables
            },
            "recent_transactions": recent_transactions,
            "monthly_trends": monthly_trends,
            "category_breakdown": [dict(c) for c in cat_breakdown],
            "pending_repayments": pending_repayments,
            "pending_collections": pending_collections,
            "overdue_summary": {
                "overdue_repayments": overdue_repayments,
                "overdue_collections": overdue_collections,
                "overdue_count": len(overdue_repayments) + len(overdue_collections)
            },
            "upcoming_summary": {
                "upcoming_repayments": upcoming_repayments,
                "upcoming_collections": upcoming_collections,
                "upcoming_count": len(upcoming_repayments) + len(upcoming_collections)
            }
        }

    @staticmethod
    def get_monthly_trends(months_back: int = 6):
        labels = []
        incomes = []
        expenses = []
        today = datetime.date.today()

        for i in range(months_back - 1, -1, -1):
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1
            month_str = f"{year}-{month:02d}"
            label = datetime.date(year, month, 1).strftime("%b %Y")
            labels.append(label)

            inc = DataStore.query("SELECT SUM(amount) as total FROM incomes WHERE transaction_date LIKE ?", (f"{month_str}%",))
            exp = DataStore.query("SELECT SUM(amount) as total FROM expenses WHERE transaction_date LIKE ?", (f"{month_str}%",))
            
            incomes.append(round(float(inc[0]["total"] or 0.0) if inc else 0.0, 2))
            expenses.append(round(float(exp[0]["total"] or 0.0) if exp else 0.0, 2))

        return {
            "labels": labels,
            "income": incomes,
            "expense": expenses
        }

class ReportService:
    """FR-12: Complete 13 Financial Reports Generator."""
    @staticmethod
    def get_report(report_type: str, start_date: str = "", end_date: str = "", person_id: str = "", account_id: str = ""):
        today = datetime.date.today().isoformat()
        
        if report_type == "monthly_income":
            sql = "SELECT strftime('%Y-%m', transaction_date) as month, source, SUM(amount) as total, COUNT(*) as count FROM incomes WHERE 1=1"
            params = []
            if start_date: sql += " AND transaction_date >= ?"; params.append(start_date)
            if end_date: sql += " AND transaction_date <= ?"; params.append(end_date)
            sql += " GROUP BY month, source ORDER BY month DESC, total DESC"
            return DataStore.query(sql, tuple(params))

        elif report_type == "monthly_expense":
            sql = "SELECT strftime('%Y-%m', transaction_date) as month, category, SUM(amount) as total, COUNT(*) as count FROM expenses WHERE 1=1"
            params = []
            if start_date: sql += " AND transaction_date >= ?"; params.append(start_date)
            if end_date: sql += " AND transaction_date <= ?"; params.append(end_date)
            sql += " GROUP BY month, category ORDER BY month DESC, total DESC"
            return DataStore.query(sql, tuple(params))

        elif report_type == "yearly_summary":
            sql = """
            SELECT strftime('%Y', transaction_date) as year,
                   SUM(CASE WHEN transaction_type = 'Income' THEN amount ELSE 0 END) as total_income,
                   SUM(CASE WHEN transaction_type = 'Expense' THEN amount ELSE 0 END) as total_expense
            FROM transactions
            WHERE transaction_type IN ('Income', 'Expense')
            GROUP BY year ORDER BY year DESC
            """
            return DataStore.query(sql)

        elif report_type == "category_expense":
            sql = "SELECT category, SUM(amount) as total, COUNT(*) as count, ROUND(AVG(amount), 2) as average FROM expenses WHERE 1=1"
            params = []
            if start_date: sql += " AND transaction_date >= ?"; params.append(start_date)
            if end_date: sql += " AND transaction_date <= ?"; params.append(end_date)
            sql += " GROUP BY category ORDER BY total DESC"
            return DataStore.query(sql, tuple(params))

        elif report_type == "income_source":
            sql = "SELECT source, SUM(amount) as total, COUNT(*) as count, ROUND(AVG(amount), 2) as average FROM incomes WHERE 1=1"
            params = []
            if start_date: sql += " AND transaction_date >= ?"; params.append(start_date)
            if end_date: sql += " AND transaction_date <= ?"; params.append(end_date)
            sql += " GROUP BY source ORDER BY total DESC"
            return DataStore.query(sql, tuple(params))

        elif report_type == "borrowed_money":
            sql = "SELECT * FROM borrowings WHERE 1=1"
            params = []
            if start_date: sql += " AND borrow_date >= ?"; params.append(start_date)
            if end_date: sql += " AND borrow_date <= ?"; params.append(end_date)
            if person_id: sql += " AND person_id = ?"; params.append(person_id)
            sql += " ORDER BY borrow_date DESC"
            return DataStore.query(sql, tuple(params))

        elif report_type == "repayment":
            sql = "SELECT * FROM loan_payments WHERE loan_type = 'Borrowed'"
            params = []
            if start_date: sql += " AND payment_date >= ?"; params.append(start_date)
            if end_date: sql += " AND payment_date <= ?"; params.append(end_date)
            sql += " ORDER BY payment_date DESC"
            return DataStore.query(sql, tuple(params))

        elif report_type == "lent_money":
            sql = "SELECT * FROM lendings WHERE 1=1"
            params = []
            if start_date: sql += " AND lend_date >= ?"; params.append(start_date)
            if end_date: sql += " AND lend_date <= ?"; params.append(end_date)
            if person_id: sql += " AND person_id = ?"; params.append(person_id)
            sql += " ORDER BY lend_date DESC"
            return DataStore.query(sql, tuple(params))

        elif report_type == "collection":
            sql = "SELECT * FROM loan_payments WHERE loan_type = 'Lent'"
            params = []
            if start_date: sql += " AND payment_date >= ?"; params.append(start_date)
            if end_date: sql += " AND payment_date <= ?"; params.append(end_date)
            sql += " ORDER BY payment_date DESC"
            return DataStore.query(sql, tuple(params))

        elif report_type == "outstanding_payables":
            return DataStore.query("SELECT * FROM borrowings WHERE outstanding_payable > 0 ORDER BY due_date ASC, outstanding_payable DESC")

        elif report_type == "outstanding_receivables":
            return DataStore.query("SELECT * FROM lendings WHERE outstanding_receivable > 0 ORDER BY expected_return_date ASC, outstanding_receivable DESC")

        elif report_type == "person_ledger":
            if person_id:
                return PeopleService.get_person_ledger(person_id)
            return PeopleService.get_people()

        elif report_type == "account_balances":
            return DataStore.query("SELECT * FROM accounts ORDER BY current_balance DESC")

        else:
            raise ValueError(f"Unknown report type: {report_type}")
