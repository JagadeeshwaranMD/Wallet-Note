"""
Storage and Data Access Layer for Wallet Note.
Integrates directly with Zoho Catalyst Data Store and provides resilient local caching.
"""

import os
import json
import sqlite3
import datetime
from typing import Dict, List, Any, Optional
import catalyst_client as cc

DB_FILE = os.path.join(os.path.dirname(__file__), "wallet_note_local.db")

def init_local_cache_db():
    """Initializes a local SQLite database that mirrors the Catalyst schema for speed and offline resilience."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        ROWID TEXT PRIMARY KEY,
        account_name TEXT NOT NULL,
        account_type TEXT NOT NULL,
        opening_balance REAL DEFAULT 0,
        current_balance REAL DEFAULT 0,
        currency TEXT DEFAULT 'INR',
        status TEXT DEFAULT 'Active',
        account_number TEXT,
        bank_name TEXT,
        notes TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS people (
        ROWID TEXT PRIMARY KEY,
        person_ref TEXT,
        full_name TEXT NOT NULL,
        mobile_number TEXT,
        email TEXT,
        address TEXT,
        notes TEXT,
        status TEXT DEFAULT 'Active',
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        ROWID TEXT PRIMARY KEY,
        category_name TEXT NOT NULL,
        category_type TEXT NOT NULL,
        is_default INTEGER DEFAULT 0,
        icon TEXT,
        color TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS incomes (
        ROWID TEXT PRIMARY KEY,
        income_ref TEXT NOT NULL,
        source TEXT NOT NULL,
        amount REAL NOT NULL,
        received_from TEXT,
        transaction_date TEXT NOT NULL,
        account_id TEXT,
        account_name TEXT,
        payment_method TEXT,
        description TEXT,
        attachment_url TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        ROWID TEXT PRIMARY KEY,
        expense_ref TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        paid_to TEXT,
        transaction_date TEXT NOT NULL,
        account_id TEXT,
        account_name TEXT,
        payment_method TEXT,
        description TEXT,
        attachment_url TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS borrowings (
        ROWID TEXT PRIMARY KEY,
        borrow_ref TEXT NOT NULL,
        person_id TEXT,
        person_name TEXT NOT NULL,
        mobile_number TEXT,
        borrowed_amount REAL NOT NULL,
        total_repaid REAL DEFAULT 0,
        outstanding_payable REAL DEFAULT 0,
        borrow_date TEXT NOT NULL,
        due_date TEXT,
        receiving_account_id TEXT,
        receiving_account_name TEXT,
        interest_info TEXT,
        notes TEXT,
        status TEXT DEFAULT 'Pending',
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS lendings (
        ROWID TEXT PRIMARY KEY,
        lend_ref TEXT NOT NULL,
        person_id TEXT,
        person_name TEXT NOT NULL,
        mobile_number TEXT,
        lent_amount REAL NOT NULL,
        total_collected REAL DEFAULT 0,
        outstanding_receivable REAL DEFAULT 0,
        lend_date TEXT NOT NULL,
        expected_return_date TEXT,
        disbursement_account_id TEXT,
        disbursement_account_name TEXT,
        interest_info TEXT,
        notes TEXT,
        status TEXT DEFAULT 'Pending',
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS loan_payments (
        ROWID TEXT PRIMARY KEY,
        payment_ref TEXT NOT NULL,
        loan_type TEXT NOT NULL,
        loan_id TEXT NOT NULL,
        loan_ref TEXT,
        person_id TEXT,
        person_name TEXT,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        account_id TEXT,
        account_name TEXT,
        payment_method TEXT,
        notes TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS account_transfers (
        ROWID TEXT PRIMARY KEY,
        transfer_ref TEXT NOT NULL,
        from_account_id TEXT NOT NULL,
        from_account_name TEXT,
        to_account_id TEXT NOT NULL,
        to_account_name TEXT,
        amount REAL NOT NULL,
        transfer_date TEXT NOT NULL,
        notes TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        ROWID TEXT PRIMARY KEY,
        transaction_ref TEXT NOT NULL,
        transaction_date TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        amount REAL NOT NULL,
        account_id TEXT,
        account_name TEXT,
        person_id TEXT,
        person_name TEXT,
        category TEXT,
        related_ref TEXT,
        description TEXT,
        notes TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        ROWID TEXT PRIMARY KEY,
        reminder_type TEXT NOT NULL,
        related_loan_id TEXT,
        related_ref TEXT,
        person_name TEXT,
        amount REAL DEFAULT 0,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'Active',
        notes TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        ROWID TEXT PRIMARY KEY,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        CREATEDTIME TEXT,
        MODIFIEDTIME TEXT
    )""")

    conn.commit()
    conn.close()

init_local_cache_db()

class DataStore:
    """Unified Data Store that communicates with Zoho Catalyst Data Store and caches in local DB."""

    @staticmethod
    def get_db():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def sync_from_catalyst(cls, table_name: str):
        """Fetches all rows from Zoho Catalyst Data Store for a table and updates local cache."""
        try:
            catalyst_rows = cc.get_all_rows(table_name)
            conn = cls.get_db()
            c = conn.cursor()
            
            # Clear existing cached table rows
            c.execute(f"DELETE FROM {table_name}")
            
            for row in catalyst_rows:
                # Filter keys that match table columns
                cols = []
                vals = []
                for k, v in row.items():
                    cols.append(k)
                    vals.append(v)
                if cols:
                    placeholders = ", ".join(["?"] * len(cols))
                    col_names = ", ".join(cols)
                    c.execute(f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})", vals)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Sync Warning] Failed to sync {table_name} from Catalyst: {e}")
            return False

    @classmethod
    def sync_all_from_catalyst(cls):
        tables = [
            "categories", "accounts", "people", "incomes", "expenses",
            "borrowings", "lendings", "loan_payments", "account_transfers",
            "transactions", "reminders", "app_settings"
        ]
        for tbl in tables:
            cls.sync_from_catalyst(tbl)

    @classmethod
    def get_all(cls, table_name: str, order_by: str = "ROWID DESC") -> List[Dict[str, Any]]:
        conn = cls.get_db()
        c = conn.cursor()
        c.execute(f"SELECT * FROM {table_name} ORDER BY {order_by}")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    @classmethod
    def get_by_id(cls, table_name: str, row_id: str) -> Optional[Dict[str, Any]]:
        conn = cls.get_db()
        c = conn.cursor()
        c.execute(f"SELECT * FROM {table_name} WHERE ROWID = ?", (str(row_id),))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def insert(cls, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts into Zoho Catalyst Data Store and caches locally."""
        # 1. Clean payload for Catalyst
        catalyst_payload = {k: v for k, v in data.items() if k not in ["ROWID", "CREATEDTIME", "MODIFIEDTIME"]}
        
        row_id = None
        catalyst_row = None
        try:
            catalyst_row = cc.insert_row(table_name, catalyst_payload)
            if catalyst_row and "ROWID" in catalyst_row:
                row_id = str(catalyst_row["ROWID"])
        except Exception as e:
            print(f"[Catalyst Insert Error] table {table_name}: {e}")
            # If Catalyst fails, generate a fallback local ROWID
            row_id = f"LOCAL_{int(datetime.datetime.now().timestamp() * 1000)}"

        data_to_store = dict(data)
        data_to_store["ROWID"] = row_id
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_to_store["CREATEDTIME"] = now_str
        data_to_store["MODIFIEDTIME"] = now_str

        # Update local DB cache
        conn = cls.get_db()
        c = conn.cursor()
        cols = list(data_to_store.keys())
        vals = [data_to_store[k] for k in cols]
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        c.execute(f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})", vals)
        conn.commit()
        conn.close()

        return data_to_store

    @classmethod
    def update(cls, table_name: str, row_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates in Zoho Catalyst Data Store and local cache."""
        catalyst_payload = {k: v for k, v in data.items() if k not in ["ROWID", "CREATEDTIME", "MODIFIEDTIME"]}
        
        # If it's a Catalyst ROWID (all digits), sync update to Catalyst
        if str(row_id).isdigit():
            try:
                cc.update_row(table_name, str(row_id), catalyst_payload)
            except Exception as e:
                print(f"[Catalyst Update Error] table {table_name}, row {row_id}: {e}")

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_to_store = dict(data)
        data_to_store["MODIFIEDTIME"] = now_str
        
        conn = cls.get_db()
        c = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in data_to_store.keys()])
        vals = list(data_to_store.values()) + [str(row_id)]
        c.execute(f"UPDATE {table_name} SET {set_clause} WHERE ROWID = ?", vals)
        conn.commit()
        conn.close()

        return cls.get_by_id(table_name, row_id)

    @classmethod
    def delete(cls, table_name: str, row_id: str) -> bool:
        """Deletes from Zoho Catalyst Data Store and local cache."""
        if str(row_id).isdigit():
            try:
                cc.delete_row(table_name, str(row_id))
            except Exception as e:
                print(f"[Catalyst Delete Error] table {table_name}, row {row_id}: {e}")

        conn = cls.get_db()
        c = conn.cursor()
        c.execute(f"DELETE FROM {table_name} WHERE ROWID = ?", (str(row_id),))
        conn.commit()
        conn.close()
        return True

    @classmethod
    def query(cls, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = cls.get_db()
        c = conn.cursor()
        c.execute(sql, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

