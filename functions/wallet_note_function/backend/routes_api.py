"""
Wallet Note - REST API Blueprint
"""

from flask import Blueprint, request, jsonify
from backend.business_logic import (
    init_seed_data,
    AccountService,
    PeopleService,
    IncomeService,
    ExpenseService,
    BorrowingService,
    LendingService,
    PaymentService,
    DashboardService,
    ReportService,
    NotificationService
)
from backend.storage import DataStore

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Ensure seeds are initialized
init_seed_data()

@api_bp.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "app": "Wallet Note", "version": "1.0.0"})

# --- Dashboard ---
@api_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    data = DashboardService.get_dashboard_data(start_date, end_date)
    return jsonify({"status": "success", "data": data})

# --- Accounts ---
@api_bp.route("/accounts", methods=["GET"])
def list_accounts():
    accounts = AccountService.get_accounts()
    return jsonify({"status": "success", "data": accounts})

@api_bp.route("/accounts", methods=["POST"])
def create_account():
    data = request.json or {}
    try:
        acc = AccountService.create_account(data)
        return jsonify({"status": "success", "data": acc, "message": "Account created successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/accounts/<account_id>", methods=["GET"])
def get_account_detail(account_id):
    acc = AccountService.get_account(account_id)
    if not acc:
        return jsonify({"status": "error", "message": "Account not found"}), 404
    # Include account transactions
    txns = DataStore.query("SELECT * FROM transactions WHERE account_id = ? ORDER BY transaction_date DESC, ROWID DESC LIMIT 50", (account_id,))
    acc["transactions"] = txns
    return jsonify({"status": "success", "data": acc})

@api_bp.route("/accounts/<account_id>", methods=["PUT"])
def update_account(account_id):
    data = request.json or {}
    try:
        acc = AccountService.update_account(account_id, data)
        return jsonify({"status": "success", "data": acc, "message": "Account updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/accounts/<account_id>", methods=["DELETE"])
def deactivate_account(account_id):
    try:
        AccountService.deactivate_account(account_id)
        return jsonify({"status": "success", "message": "Account deactivated safely"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/accounts/transfer", methods=["POST"])
def transfer_funds():
    data = request.json or {}
    try:
        res = AccountService.transfer_funds(
            from_account_id=data.get("from_account_id"),
            to_account_id=data.get("to_account_id"),
            amount=data.get("amount"),
            transfer_date=data.get("transfer_date"),
            notes=data.get("notes", "")
        )
        return jsonify({"status": "success", "data": res, "message": "Funds transferred successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Categories ---
@api_bp.route("/categories", methods=["GET"])
def get_categories():
    cat_type = request.args.get("type", "")
    if cat_type:
        cats = DataStore.query("SELECT * FROM categories WHERE category_type = ? ORDER BY category_name ASC", (cat_type,))
    else:
        cats = DataStore.get_all("categories", order_by="category_type DESC, category_name ASC")
    return jsonify({"status": "success", "data": cats})

@api_bp.route("/categories", methods=["POST"])
def create_category():
    try:
        data = request.json or {}
        name = str(data.get("category_name", "")).strip()
        c_type = str(data.get("category_type", "Expense")).strip()
        if not name:
            return jsonify({"status": "error", "message": "Category name is required"}), 400
        res = DataStore.insert("categories", {
            "category_name": name,
            "category_type": c_type,
            "is_default": False,
            "icon": data.get("icon", "tag"),
            "color": data.get("color", "#6366f1")
        })
        return jsonify({"status": "success", "data": res, "message": "Category added successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/categories/<category_id>", methods=["DELETE"])
def delete_category(category_id):
    try:
        DataStore.delete("categories", category_id)
        return jsonify({"status": "success", "message": "Category deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Incomes ---
@api_bp.route("/incomes", methods=["GET"])
def get_incomes():
    search = request.args.get("search", "")
    account_id = request.args.get("account_id", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    incomes = IncomeService.get_incomes(search, account_id, start_date, end_date)
    return jsonify({"status": "success", "data": incomes})

@api_bp.route("/incomes", methods=["POST"])
def create_income():
    data = request.json or {}
    try:
        inc = IncomeService.create_income(data)
        return jsonify({"status": "success", "data": inc, "message": "Income recorded successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/incomes/<income_id>", methods=["GET"])
def get_income(income_id):
    inc = DataStore.get_by_id("incomes", income_id)
    if not inc:
        return jsonify({"status": "error", "message": "Income record not found"}), 404
    return jsonify({"status": "success", "data": inc})

@api_bp.route("/incomes/<income_id>", methods=["PUT"])
def update_income(income_id):
    data = request.json or {}
    try:
        inc = IncomeService.update_income(income_id, data)
        return jsonify({"status": "success", "data": inc, "message": "Income updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/incomes/<income_id>", methods=["DELETE"])
def delete_income(income_id):
    try:
        IncomeService.delete_income(income_id)
        return jsonify({"status": "success", "message": "Income record deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Expenses ---
@api_bp.route("/expenses", methods=["GET"])
def get_expenses():
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    account_id = request.args.get("account_id", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    expenses = ExpenseService.get_expenses(search, category, account_id, start_date, end_date)
    return jsonify({"status": "success", "data": expenses})

@api_bp.route("/expenses", methods=["POST"])
def create_expense():
    data = request.json or {}
    try:
        exp = ExpenseService.create_expense(data)
        return jsonify({"status": "success", "data": exp, "message": "Expense recorded successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/expenses/<expense_id>", methods=["GET"])
def get_expense(expense_id):
    exp = DataStore.get_by_id("expenses", expense_id)
    if not exp:
        return jsonify({"status": "error", "message": "Expense record not found"}), 404
    return jsonify({"status": "success", "data": exp})

@api_bp.route("/expenses/<expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.json or {}
    try:
        exp = ExpenseService.update_expense(expense_id, data)
        return jsonify({"status": "success", "data": exp, "message": "Expense updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/expenses/<expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    try:
        ExpenseService.delete_expense(expense_id)
        return jsonify({"status": "success", "message": "Expense record deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Borrowed Money Management (FR-04) ---
@api_bp.route("/borrowings", methods=["GET"])
def get_borrowings():
    status = request.args.get("status", "")
    person_id = request.args.get("person_id", "")
    rows = BorrowingService.get_borrowings(status, person_id)
    return jsonify({"status": "success", "data": rows})

@api_bp.route("/borrowings", methods=["POST"])
def create_borrowing():
    data = request.json or {}
    try:
        bor = BorrowingService.create_borrowing(data)
        return jsonify({"status": "success", "data": bor, "message": "Borrowed money recorded successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/borrowings/<borrow_id>", methods=["GET"])
def get_borrowing_detail(borrow_id):
    bor = BorrowingService.get_borrowing(borrow_id)
    if not bor:
        return jsonify({"status": "error", "message": "Borrowing record not found"}), 404
    return jsonify({"status": "success", "data": bor})

@api_bp.route("/borrowings/<borrow_id>/repay", methods=["POST"])
def repay_borrowing(borrow_id):
    data = request.json or {}
    try:
        res = PaymentService.record_repayment(
            borrow_id=borrow_id,
            amount=data.get("amount"),
            payment_date=data.get("payment_date"),
            account_id=data.get("account_id"),
            payment_method=data.get("payment_method", "Bank Transfer"),
            notes=data.get("notes", "")
        )
        return jsonify({"status": "success", "data": res, "message": "Repayment recorded successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Lent Money Management (FR-05) ---
@api_bp.route("/lendings", methods=["GET"])
def get_lendings():
    status = request.args.get("status", "")
    person_id = request.args.get("person_id", "")
    rows = LendingService.get_lendings(status, person_id)
    return jsonify({"status": "success", "data": rows})

@api_bp.route("/lendings", methods=["POST"])
def create_lending():
    data = request.json or {}
    try:
        lnd = LendingService.create_lending(data)
        return jsonify({"status": "success", "data": lnd, "message": "Lent money recorded successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/lendings/<lend_id>", methods=["GET"])
def get_lending_detail(lend_id):
    lnd = LendingService.get_lending(lend_id)
    if not lnd:
        return jsonify({"status": "error", "message": "Lending record not found"}), 404
    return jsonify({"status": "success", "data": lnd})

@api_bp.route("/lendings/<lend_id>/collect", methods=["POST"])
def collect_lending(lend_id):
    data = request.json or {}
    try:
        res = PaymentService.record_collection(
            lend_id=lend_id,
            amount=data.get("amount"),
            payment_date=data.get("payment_date"),
            account_id=data.get("account_id"),
            payment_method=data.get("payment_method", "Bank Transfer"),
            notes=data.get("notes", "")
        )
        return jsonify({"status": "success", "data": res, "message": "Collection recorded successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Loan Payment Deletion ---
@api_bp.route("/loan_payments/<payment_id>", methods=["DELETE"])
def delete_loan_payment(payment_id):
    try:
        PaymentService.delete_payment(payment_id)
        return jsonify({"status": "success", "message": "Payment record deleted and balances updated"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- People & Personal Ledger (FR-07, FR-08) ---
@api_bp.route("/people", methods=["GET"])
def get_people():
    people = PeopleService.get_people()
    return jsonify({"status": "success", "data": people})

@api_bp.route("/people", methods=["POST"])
def create_person():
    data = request.json or {}
    try:
        p = PeopleService.create_person(data)
        return jsonify({"status": "success", "data": p, "message": "Person added successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/people/<person_id>", methods=["GET"])
def get_person(person_id):
    p = PeopleService.get_person(person_id)
    if not p:
        return jsonify({"status": "error", "message": "Person not found"}), 404
    return jsonify({"status": "success", "data": p})

@api_bp.route("/people/<person_id>", methods=["PUT"])
def update_person(person_id):
    data = request.json or {}
    try:
        p = PeopleService.update_person(person_id, data)
        return jsonify({"status": "success", "data": p, "message": "Person updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/people/<person_id>", methods=["DELETE"])
def delete_person(person_id):
    try:
        PeopleService.delete_person(person_id)
        return jsonify({"status": "success", "message": "Person removed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/people/<person_id>/ledger", methods=["GET"])
def get_person_ledger(person_id):
    try:
        ledger = PeopleService.get_person_ledger(person_id)
        return jsonify({"status": "success", "data": ledger})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Unified Transaction History (FR-09) ---
@api_bp.route("/transactions", methods=["GET"])
def get_transactions():
    search = request.args.get("search", "")
    txn_type = request.args.get("type", "")
    account_id = request.args.get("account_id", "")
    person_name = request.args.get("person", "")
    category = request.args.get("category", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    sql = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if search:
        sql += " AND (description LIKE ? OR notes LIKE ? OR transaction_ref LIKE ? OR person_name LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    if txn_type:
        sql += " AND transaction_type = ?"
        params.append(txn_type)
    if account_id:
        sql += " AND account_id = ?"
        params.append(account_id)
    if person_name:
        sql += " AND person_name LIKE ?"
        params.append(f"%{person_name}%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    if start_date:
        sql += " AND transaction_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND transaction_date <= ?"
        params.append(end_date)

    sql += " ORDER BY transaction_date DESC, ROWID DESC LIMIT 200"
    rows = DataStore.query(sql, tuple(params))
    return jsonify({"status": "success", "data": rows})

# --- Reminders (FR-11) ---
@api_bp.route("/reminders", methods=["GET"])
def get_reminders():
    # Evaluate dynamic reminders
    dash = DashboardService.get_dashboard_data()
    return jsonify({
        "status": "success",
        "data": {
            "overdue_repayments": dash["overdue_summary"]["overdue_repayments"],
            "overdue_collections": dash["overdue_summary"]["overdue_collections"],
            "upcoming_repayments": dash["upcoming_summary"]["upcoming_repayments"],
            "upcoming_collections": dash["upcoming_summary"]["upcoming_collections"]
        }
    })

# --- Reports & Analytics (FR-12) ---
@api_bp.route("/reports/<report_type>", methods=["GET"])
def get_report(report_type):
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    person_id = request.args.get("person_id", "")
    account_id = request.args.get("account_id", "")
    try:
        report_data = ReportService.get_report(report_type, start_date, end_date, person_id, account_id)
        return jsonify({"status": "success", "report_type": report_type, "data": report_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Automated SMS Notification Dispatcher ---
@api_bp.route("/notifications/send", methods=["POST"])
@api_bp.route("/sms/send", methods=["POST"])
def send_manual_notification():
    data = request.json or {}
    phone = data.get("phone_number")
    notif_type = data.get("notification_type", "loan_given")
    details = data.get("details") or {}
    if not phone:
        return jsonify({"status": "error", "message": "Phone number is required."}), 400
    try:
        res = NotificationService.dispatch_sms(phone, notif_type, details)
        return jsonify({"status": "success", "data": res, "message": "SMS dispatched successfully to contact"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/notifications/preview", methods=["POST"])
@api_bp.route("/sms/preview", methods=["POST"])
def preview_notification():
    data = request.json or {}
    notif_type = data.get("notification_type", "loan_given")
    details = data.get("details") or {}
    phone = data.get("phone_number", "")
    try:
        norm_phone = NotificationService.normalize_phone_number(phone) if phone else ""
        msg = NotificationService.generate_sms_message(notif_type, details)
        return jsonify({
            "status": "success",
            "data": {
                "message_text": msg,
                "phone_number": norm_phone or phone,
                "recipient_name": details.get("person_name") or "",
                "notification_type": notif_type
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/sms/test", methods=["POST"])
def test_sms_dispatch():
    data = request.json or {}
    phone = data.get("phone_number")
    if not phone:
        return jsonify({"status": "error", "message": "Phone number is required."}), 400
    try:
        res = NotificationService.dispatch_sms(
            phone_number=phone,
            notification_type="loan_given",
            details={
                "person_name": data.get("person_name", "Valued Contact"),
                "amount": float(data.get("amount", 5000.0)),
                "reference": "TEST-SMS-01",
                "due_date": "30-Nov-2026",
                "account_name": "Cash Wallet",
                "notes": "Test SMS dispatch verification"
            }
        )
        return jsonify({"status": "success", "data": res, "message": "Test SMS sent successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# --- Settings & Data Management (FR-13) ---
@api_bp.route("/settings", methods=["GET"])
def get_settings():
    rows = DataStore.get_all("app_settings")
    settings_dict = {r["setting_key"]: r["setting_value"] for r in rows}
    return jsonify({"status": "success", "data": settings_dict})

@api_bp.route("/settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    for k, v in data.items():
        existing = DataStore.query("SELECT ROWID FROM app_settings WHERE setting_key = ?", (k,))
        if existing:
            DataStore.update("app_settings", existing[0]["ROWID"], {"setting_value": str(v)})
        else:
            DataStore.insert("app_settings", {"setting_key": k, "setting_value": str(v)})
    return jsonify({"status": "success", "message": "Settings saved"})

# --- Zoho Catalyst Data Store Sync ---
@api_bp.route("/sync/catalyst", methods=["POST"])
def trigger_sync():
    try:
        DataStore.sync_all_from_catalyst()
        return jsonify({"status": "success", "message": "Successfully synchronized with Zoho Catalyst Data Store"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

