"""
Zoho Catalyst Python Client
Connects seamlessly to Zoho Catalyst Data Store & ZCQL for the Wallet Note project.
"""

import os
import json
import time
import subprocess
import requests

PROJECT_ID = "41833000000087004"
CATALYST_BASE_URL = f"https://api.catalyst.zoho.in/baas/v1/project/{PROJECT_ID}"
ENVIRONMENT = "Development"

# Cache token in memory
_CACHED_TOKEN = None
_TOKEN_EXPIRES_AT = 0

# Table name to table ID map in Catalyst
TABLE_IDS = {
    "accounts": "41833000000484004",
    "people": "41833000000479002",
    "categories": "41833000000475390",
    "incomes": "41833000000485360",
    "expenses": "41833000000475749",
    "borrowings": "41833000000488001",
    "lendings": "41833000000481004",
    "loan_payments": "41833000000476017",
    "account_transfers": "41833000000487108",
    "transactions": "41833000000488360",
    "reminders": "41833000000489001",
    "app_settings": "41833000000489360"
}

def get_catalyst_access_token():
    global _CACHED_TOKEN, _TOKEN_EXPIRES_AT
    now = time.time() * 1000  # in ms
    if _CACHED_TOKEN and _TOKEN_EXPIRES_AT > (now + 60000):
        return _CACHED_TOKEN

    env_token = os.environ.get("CATALYST_ACCESS_TOKEN")
    if env_token:
        _CACHED_TOKEN = env_token
        _TOKEN_EXPIRES_AT = now + 3600000
        return _CACHED_TOKEN

    # Read from local Catalyst CLI configuration via node
    node_script = """
    const Credential = require('C:/Users/Jaga/AppData/Roaming/npm/node_modules/zcatalyst-cli/lib/authentication/credential.js').default;
    const config = require('C:/Users/Jaga/AppData/Roaming/npm/node_modules/zcatalyst-cli/lib/util_modules/config-store.js').default;
    const dec = Credential.crypt.decrypt(config.get('in.credential'));
    console.log(JSON.stringify({ token: dec.access_token, expires_at: dec.expires_at }));
    """
    try:
        proc = subprocess.run(["node", "-e", node_script], capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout.strip())
        _CACHED_TOKEN = data["token"]
        _TOKEN_EXPIRES_AT = data["expires_at"]
        return _CACHED_TOKEN
    except Exception as e:
        print(f"[Catalyst Client] Error getting token from CLI: {e}")
        return None

def _get_headers(zcql=False):
    token = get_catalyst_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.catalyst.v2+zcql" if zcql else "application/vnd.catalyst.v2+json",
        "X-CATALYST-Environment": ENVIRONMENT
    }
    return headers

def execute_zcql(query: str):
    """Execute a ZCQL query against Catalyst Data Store."""
    headers = _get_headers(zcql=True)
    url = f"{CATALYST_BASE_URL}/query"
    resp = requests.post(url, headers=headers, json={"query": query})
    if resp.status_code == 200:
        data = resp.json().get("data", [])
        # Catalyst ZCQL returns [{ "table_name": { fields... } }]
        flattened = []
        for item in data:
            if isinstance(item, dict):
                # If wrapped with table name
                first_val = next(iter(item.values()))
                if isinstance(first_val, dict):
                    flattened.append(first_val)
                else:
                    flattened.append(item)
            else:
                flattened.append(item)
        return flattened
    else:
        print(f"[Catalyst ZCQL Error] Status {resp.status_code}: {resp.text}")
        raise RuntimeError(f"ZCQL failed: {resp.text}")

def get_table_identifier(table_name_or_id: str):
    return TABLE_IDS.get(table_name_or_id, table_name_or_id)

def insert_rows(table_name: str, rows: list):
    table_id = get_table_identifier(table_name)
    headers = _get_headers(zcql=False)
    url = f"{CATALYST_BASE_URL}/table/{table_id}/row"
    resp = requests.post(url, headers=headers, json=rows)
    if resp.status_code == 200:
        return resp.json().get("data", [])
    else:
        print(f"[Catalyst Insert Error] Status {resp.status_code}: {resp.text}")
        raise RuntimeError(f"Insert failed: {resp.text}")

def insert_row(table_name: str, row: dict):
    res = insert_rows(table_name, [row])
    return res[0] if res else None

def update_row(table_name: str, row_id: str, updated_data: dict):
    table_id = get_table_identifier(table_name)
    headers = _get_headers(zcql=False)
    url = f"{CATALYST_BASE_URL}/table/{table_id}/row"
    payload = [dict(updated_data, ROWID=str(row_id))]
    resp = requests.patch(url, headers=headers, json=payload)
    if resp.status_code == 200:
        res = resp.json().get("data", [])
        return res[0] if res else {}
    else:
        print(f"[Catalyst Update Error] Status {resp.status_code}: {resp.text}")
        raise RuntimeError(f"Update failed: {resp.text}")

def delete_row(table_name: str, row_id: str):
    table_id = get_table_identifier(table_name)
    headers = _get_headers(zcql=False)
    url = f"{CATALYST_BASE_URL}/table/{table_id}/row/{row_id}"
    resp = requests.delete(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("data", {})
    else:
        print(f"[Catalyst Delete Error] Status {resp.status_code}: {resp.text}")
        raise RuntimeError(f"Delete failed: {resp.text}")

def get_row(table_name: str, row_id: str):
    table_id = get_table_identifier(table_name)
    headers = _get_headers(zcql=False)
    url = f"{CATALYST_BASE_URL}/table/{table_id}/row/{row_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("data", {})
    else:
        print(f"[Catalyst Get Error] Status {resp.status_code}: {resp.text}")
        raise RuntimeError(f"Get failed: {resp.text}")

def get_all_rows(table_name: str):
    return execute_zcql(f"SELECT * FROM {table_name}")

if __name__ == "__main__":
    print("Testing Catalyst Python Client...")
    token = get_catalyst_access_token()
    print("Access token acquired:", bool(token))
    rows = get_all_rows("categories")
    print(f"Categories count: {len(rows)}")
