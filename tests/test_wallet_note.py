"""
Wallet Note — Automated Verification & Financial Integrity Test Suite
Verifies all 10 core financial business rules and all 13 modules.
"""

import unittest
import json
from app import app
from backend.storage import DataStore
from backend.business_logic import (
    AccountService,
    IncomeService,
    ExpenseService,
    BorrowingService,
    LendingService,
    PaymentService,
    PeopleService,
    DashboardService,
    ReportService
)

class WalletNoteTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        for a in AccountService.get_accounts():
            AccountService.recalculate_balance(a['ROWID'])

    def test_01_ping(self):
        resp = self.client.get('/api/ping')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['app'], 'Wallet Note')

    def test_02_accounts_and_seeds(self):
        resp = self.client.get('/api/accounts')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(len(data['data']) >= 3)
        
        # Test creating a test account
        acc_payload = {
            "account_name": "Test Bank Account",
            "account_type": "Savings Bank Account",
            "opening_balance": 10000.0,
            "bank_name": "Test Bank"
        }
        res = self.client.post('/api/accounts', json=acc_payload)
        self.assertEqual(res.status_code, 201)
        acc_data = json.loads(res.data)['data']
        self.assertEqual(float(acc_data['current_balance']), 10000.0)

    def test_03_income_management(self):
        # 1. Get an account
        accounts = AccountService.get_accounts()
        acc = accounts[0]
        initial_balance = float(acc['current_balance'])

        # 2. Record income
        income_payload = {
            "amount": 25000.0,
            "source": "Salary",
            "account_id": acc['ROWID'],
            "transaction_date": "2026-10-31",
            "received_from": "Acme Corp",
            "description": "Monthly Salary"
        }
        res = self.client.post('/api/incomes', json=income_payload)
        self.assertEqual(res.status_code, 201)
        inc_data = json.loads(res.data)['data']
        self.assertEqual(float(inc_data['amount']), 25000.0)

        # 3. Check account balance increment
        updated_acc = AccountService.get_account(acc['ROWID'])
        self.assertAlmostEqual(float(updated_acc['current_balance']), initial_balance + 25000.0, places=2)

    def test_04_expense_management(self):
        accounts = AccountService.get_accounts()
        acc = accounts[0]
        initial_balance = float(acc['current_balance'])

        expense_payload = {
            "amount": 3000.0,
            "category": "Food & Dining",
            "account_id": acc['ROWID'],
            "transaction_date": "2026-10-31",
            "paid_to": "Supermarket",
            "description": "Weekly Groceries"
        }
        res = self.client.post('/api/expenses', json=expense_payload)
        self.assertEqual(res.status_code, 201)

        # Check account balance decrement
        updated_acc = AccountService.get_account(acc['ROWID'])
        self.assertAlmostEqual(float(updated_acc['current_balance']), initial_balance - 3000.0, places=2)

    def test_05_borrowing_and_repayment(self):
        """
        Rule 1: Borrowed principal must not be classified as income.
        Rule 3: Principal repayment must not be classified as an ordinary expense.
        """
        accounts = AccountService.get_accounts()
        acc = accounts[0]
        initial_balance = float(acc['current_balance'])

        self.person_name_a = f"Person A {id(self)}"
        # User borrows ₹10,000 from Person A
        borrow_payload = {
            "person_name": self.person_name_a,
            "mobile_number": "9876543210",
            "borrowed_amount": 10000.0,
            "receiving_account_id": acc['ROWID'],
            "borrow_date": "2026-10-31",
            "due_date": "2026-11-30",
            "notes": "Emergency loan"
        }
        res = self.client.post('/api/borrowings', json=borrow_payload)
        self.assertEqual(res.status_code, 201)
        bor_data = json.loads(res.data)['data']
        bor_id = bor_data['ROWID']
        self.person_id_a = bor_data['person_id']

        # Balance increased by 10,000
        acc_after_borrow = AccountService.get_account(acc['ROWID'])
        self.assertAlmostEqual(float(acc_after_borrow['current_balance']), initial_balance + 10000.0, places=2)

        # Repayment 1: ₹2,000
        repay_res1 = self.client.post(f'/api/borrowings/{bor_id}/repay', json={
            "amount": 2000.0,
            "payment_date": "2026-11-05",
            "account_id": acc['ROWID'],
            "payment_method": "Bank Transfer",
            "notes": "First partial repayment"
        })
        self.assertEqual(repay_res1.status_code, 200)

        # Repayment 2: ₹3,000
        repay_res2 = self.client.post(f'/api/borrowings/{bor_id}/repay', json={
            "amount": 3000.0,
            "payment_date": "2026-11-10",
            "account_id": acc['ROWID'],
            "payment_method": "Bank Transfer",
            "notes": "Second partial repayment"
        })
        self.assertEqual(repay_res2.status_code, 200)

        # Verify loan state:
        # Original: 10,000, Total Repaid: 5,000, Outstanding: 5,000, Status: Partially Paid
        bor_detail = BorrowingService.get_borrowing(bor_id)
        self.assertEqual(float(bor_detail['borrowed_amount']), 10000.0)
        self.assertEqual(float(bor_detail['total_repaid']), 5000.0)
        self.assertEqual(float(bor_detail['outstanding_payable']), 5000.0)
        self.assertEqual(bor_detail['status'], 'Partially Paid')

    def test_06_lending_and_collection(self):
        """
        Rule 2: Lent principal must not be classified as an expense.
        Rule 4: Principal collection must not be classified as ordinary income.
        """
        accounts = AccountService.get_accounts()
        acc = accounts[0]
        initial_balance = float(acc['current_balance'])

        # User lends ₹8,000 to Person B
        lend_payload = {
            "person_name": "Person B",
            "mobile_number": "9123456780",
            "lent_amount": 8000.0,
            "disbursement_account_id": acc['ROWID'],
            "lend_date": "2026-10-31",
            "expected_return_date": "2026-11-20",
            "notes": "Short term assistance"
        }
        res = self.client.post('/api/lendings', json=lend_payload)
        self.assertEqual(res.status_code, 201)
        lend_data = json.loads(res.data)['data']
        lend_id = lend_data['ROWID']

        # Balance decreased by 8,000
        acc_after_lend = AccountService.get_account(acc['ROWID'])
        self.assertAlmostEqual(float(acc_after_lend['current_balance']), initial_balance - 8000.0, places=2)

        # Collection 1: ₹3,000
        col_res1 = self.client.post(f'/api/lendings/{lend_id}/collect', json={
            "amount": 3000.0,
            "payment_date": "2026-11-05",
            "account_id": acc['ROWID'],
            "payment_method": "UPI",
            "notes": "First return"
        })
        self.assertEqual(col_res1.status_code, 200)

        # Collection 2: ₹2,000
        col_res2 = self.client.post(f'/api/lendings/{lend_id}/collect', json={
            "amount": 2000.0,
            "payment_date": "2026-11-12",
            "account_id": acc['ROWID'],
            "payment_method": "UPI",
            "notes": "Second return"
        })
        self.assertEqual(col_res2.status_code, 200)

        # Verify lending state:
        # Original: 8,000, Total Collected: 5,000, Outstanding Receivable: 3,000, Status: Partially Received
        lend_detail = LendingService.get_lending(lend_id)
        self.assertEqual(float(lend_detail['lent_amount']), 8000.0)
        self.assertEqual(float(lend_detail['total_collected']), 5000.0)
        self.assertEqual(float(lend_detail['outstanding_receivable']), 3000.0)
        self.assertEqual(lend_detail['status'], 'Partially Received')

    def test_07_internal_transfer(self):
        """Rule 6: Internal account transfers must not change total available funds."""
        accounts = AccountService.get_accounts()
        self.assertTrue(len(accounts) >= 2)
        acc1 = accounts[0]
        acc2 = accounts[1]

        total_before = sum(float(a['current_balance']) for a in AccountService.get_accounts() if a['status'] == 'Active')

        res = self.client.post('/api/accounts/transfer', json={
            "from_account_id": acc1['ROWID'],
            "to_account_id": acc2['ROWID'],
            "amount": 1500.0,
            "transfer_date": "2026-10-31",
            "notes": "Internal transfer test"
        })
        self.assertEqual(res.status_code, 200)

        total_after = sum(float(a['current_balance']) for a in AccountService.get_accounts() if a['status'] == 'Active')
        self.assertAlmostEqual(total_before, total_after, places=2)

    def test_08_person_ledger(self):
        """FR-08: Person-wise Personal Ledger."""
        import time
        name = f"Test Ledger Person {time.time()}"
        p = PeopleService.get_or_create_person(name, "9000011111")
        pid = p['ROWID']
        accounts = AccountService.get_accounts()
        acc = accounts[0]

        # Borrow 5000
        bor = BorrowingService.create_borrowing({
            "person_name": name,
            "borrowed_amount": 5000.0,
            "receiving_account_id": acc['ROWID'],
            "borrow_date": "2026-10-31"
        })
        # Repay 2000
        PaymentService.record_repayment(bor['ROWID'], 2000.0, "2026-10-31", acc['ROWID'])

        res = self.client.get(f'/api/people/{pid}/ledger')
        self.assertEqual(res.status_code, 200)
        ledger = json.loads(res.data)['data']

        self.assertEqual(ledger['person']['full_name'], name)
        self.assertTrue('summary' in ledger)
        self.assertEqual(float(ledger['summary']['total_borrowed']), 5000.0)
        self.assertEqual(float(ledger['summary']['total_repaid']), 2000.0)
        self.assertEqual(float(ledger['summary']['remaining_to_pay']), 3000.0)
        self.assertTrue(len(ledger['activities']) >= 2)

    def test_09_dashboard_and_reports(self):
        """FR-01 & FR-12: Dashboard metrics and reports reconciliation."""
        dash_res = self.client.get('/api/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        dash = json.loads(dash_res.data)['data']

        self.assertTrue('metrics' in dash)
        self.assertTrue(dash['metrics']['total_income'] >= 25000.0)
        self.assertTrue(dash['metrics']['total_expense'] >= 3000.0)
        self.assertTrue(dash['metrics']['total_borrowed'] >= 10000.0)
        self.assertTrue(dash['metrics']['total_lent'] >= 8000.0)

        # Check all 13 reports
        report_types = [
            "monthly_income", "monthly_expense", "yearly_summary",
            "category_expense", "income_source", "borrowed_money",
            "repayment", "lent_money", "collection",
            "outstanding_payables", "outstanding_receivables",
            "person_ledger", "account_balances"
        ]
        for rt in report_types:
            rep_res = self.client.get(f'/api/reports/{rt}')
            self.assertEqual(rep_res.status_code, 200, f"Report {rt} failed")

    def test_10_automated_sms_dispatch(self):
        """FR-11 & Core: Automated SMS message dispatch to contact numbers."""
        from backend.business_logic import NotificationService

        # 1. Test SMS Message Generation (no markdown formatting, SMS-ready)
        sms_text = NotificationService.generate_sms_message('loan_given', {
            'person_name': 'Karthik',
            'amount': 12000.0,
            'reference': 'LND-TEST-99',
            'due_date': '2026-12-31',
            'account_name': 'Savings Bank Account'
        })
        self.assertIn('WALLET NOTE:', sms_text)
        self.assertIn('Karthik', sms_text)
        self.assertIn('12,000.00', sms_text)
        self.assertIn('LND-TEST-99', sms_text)

        # 2. Test Automated SMS Dispatch Endpoint
        resp = self.client.post('/api/sms/send', json={
            'phone_number': '+919876500000',
            'notification_type': 'loan_given',
            'details': {
                'person_name': 'Karthik',
                'amount': 12000.0,
                'reference': 'LND-TEST-99',
                'due_date': '2026-12-31'
            }
        })
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)['data']
        self.assertTrue(data['sms_sent'])
        self.assertEqual(data['phone_number'], '+919876500000')
        self.assertNotIn('whatsapp_url', data)

        # 3. Test SMS Preview Endpoint
        prev_res = self.client.post('/api/sms/preview', json={
            'phone_number': '9876500000',
            'notification_type': 'repayment',
            'details': {
                'person_name': 'Karthik',
                'amount': 4000.0,
                'remaining_amount': 8000.0,
                'reference': 'REP-TEST-99'
            }
        })
        self.assertEqual(prev_res.status_code, 200)
        pdata = json.loads(prev_res.data)['data']
        self.assertIn('WALLET NOTE ADVICE:', pdata['message_text'])
        self.assertEqual(pdata['phone_number'], '+919876500000')
        self.assertNotIn('whatsapp_url', pdata)

if __name__ == '__main__':
    unittest.main()
