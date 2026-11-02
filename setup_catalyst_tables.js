const Credential = require('C:/Users/Jaga/AppData/Roaming/npm/node_modules/zcatalyst-cli/lib/authentication/credential.js').default;
const config = require('C:/Users/Jaga/AppData/Roaming/npm/node_modules/zcatalyst-cli/lib/util_modules/config-store.js').default;

const projectId = '41833000000087004';

const tablesDefinition = [
  {
    table_name: 'accounts',
    columns: [
      { column_name: 'account_name', data_type: 'varchar', max_length: 100, is_mandatory: true },
      { column_name: 'account_type', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'opening_balance', data_type: 'double', decimal_digits: 2, is_mandatory: false },
      { column_name: 'current_balance', data_type: 'double', decimal_digits: 2, is_mandatory: false },
      { column_name: 'currency', data_type: 'varchar', max_length: 10, is_mandatory: false },
      { column_name: 'status', data_type: 'varchar', max_length: 20, is_mandatory: false },
      { column_name: 'account_number', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'bank_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'notes', data_type: 'text', max_length: 10000, is_mandatory: false }
    ]
  },
  {
    table_name: 'people',
    columns: [
      { column_name: 'person_ref', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'full_name', data_type: 'varchar', max_length: 100, is_mandatory: true },
      { column_name: 'mobile_number', data_type: 'varchar', max_length: 20, is_mandatory: false },
      { column_name: 'email', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'address', data_type: 'varchar', max_length: 255, is_mandatory: false },
      { column_name: 'notes', data_type: 'text', max_length: 10000, is_mandatory: false },
      { column_name: 'status', data_type: 'varchar', max_length: 20, is_mandatory: false }
    ]
  },
  {
    table_name: 'categories',
    columns: [
      { column_name: 'category_name', data_type: 'varchar', max_length: 100, is_mandatory: true },
      { column_name: 'category_type', data_type: 'varchar', max_length: 20, is_mandatory: true },
      { column_name: 'is_default', data_type: 'boolean', is_mandatory: false },
      { column_name: 'icon', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'color', data_type: 'varchar', max_length: 20, is_mandatory: false }
    ]
  },
  {
    table_name: 'incomes',
    columns: [
      { column_name: 'income_ref', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'source', data_type: 'varchar', max_length: 100, is_mandatory: true },
      { column_name: 'amount', data_type: 'double', decimal_digits: 2, is_mandatory: true },
      { column_name: 'received_from', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'transaction_date', data_type: 'varchar', max_length: 30, is_mandatory: true },
      { column_name: 'account_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'account_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'payment_method', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'description', data_type: 'text', max_length: 10000, is_mandatory: false },
      { column_name: 'attachment_url', data_type: 'varchar', max_length: 255, is_mandatory: false }
    ]
  },
  {
    table_name: 'expenses',
    columns: [
      { column_name: 'expense_ref', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'category', data_type: 'varchar', max_length: 100, is_mandatory: true },
      { column_name: 'amount', data_type: 'double', decimal_digits: 2, is_mandatory: true },
      { column_name: 'paid_to', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'transaction_date', data_type: 'varchar', max_length: 30, is_mandatory: true },
      { column_name: 'account_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'account_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'payment_method', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'description', data_type: 'text', max_length: 10000, is_mandatory: false },
      { column_name: 'attachment_url', data_type: 'varchar', max_length: 255, is_mandatory: false }
    ]
  },
  {
    table_name: 'borrowings',
    columns: [
      { column_name: 'borrow_ref', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'person_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'person_name', data_type: 'varchar', max_length: 100, is_mandatory: true },
      { column_name: 'mobile_number', data_type: 'varchar', max_length: 20, is_mandatory: false },
      { column_name: 'borrowed_amount', data_type: 'double', decimal_digits: 2, is_mandatory: true },
      { column_name: 'total_repaid', data_type: 'double', decimal_digits: 2, is_mandatory: false },
      { column_name: 'outstanding_payable', data_type: 'double', decimal_digits: 2, is_mandatory: false },
      { column_name: 'borrow_date', data_type: 'varchar', max_length: 30, is_mandatory: true },
      { column_name: 'due_date', data_type: 'varchar', max_length: 30, is_mandatory: false },
      { column_name: 'receiving_account_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'receiving_account_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'interest_info', data_type: 'varchar', max_length: 255, is_mandatory: false },
      { column_name: 'notes', data_type: 'text', max_length: 10000, is_mandatory: false },
      { column_name: 'status', data_type: 'varchar', max_length: 30, is_mandatory: false }
    ]
  },
  {
    table_name: 'lendings',
    columns: [
      { column_name: 'lend_ref', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'person_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'person_name', data_type: 'varchar', max_length: 100, is_mandatory: true },
      { column_name: 'mobile_number', data_type: 'varchar', max_length: 20, is_mandatory: false },
      { column_name: 'lent_amount', data_type: 'double', decimal_digits: 2, is_mandatory: true },
      { column_name: 'total_collected', data_type: 'double', decimal_digits: 2, is_mandatory: false },
      { column_name: 'outstanding_receivable', data_type: 'double', decimal_digits: 2, is_mandatory: false },
      { column_name: 'lend_date', data_type: 'varchar', max_length: 30, is_mandatory: true },
      { column_name: 'expected_return_date', data_type: 'varchar', max_length: 30, is_mandatory: false },
      { column_name: 'disbursement_account_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'disbursement_account_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'interest_info', data_type: 'varchar', max_length: 255, is_mandatory: false },
      { column_name: 'notes', data_type: 'text', max_length: 10000, is_mandatory: false },
      { column_name: 'status', data_type: 'varchar', max_length: 30, is_mandatory: false }
    ]
  },
  {
    table_name: 'loan_payments',
    columns: [
      { column_name: 'payment_ref', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'loan_type', data_type: 'varchar', max_length: 20, is_mandatory: true },
      { column_name: 'loan_id', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'loan_ref', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'person_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'person_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'amount', data_type: 'double', decimal_digits: 2, is_mandatory: true },
      { column_name: 'payment_date', data_type: 'varchar', max_length: 30, is_mandatory: true },
      { column_name: 'account_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'account_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'payment_method', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'notes', data_type: 'text', max_length: 10000, is_mandatory: false }
    ]
  },
  {
    table_name: 'account_transfers',
    columns: [
      { column_name: 'transfer_ref', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'from_account_id', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'from_account_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'to_account_id', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'to_account_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'amount', data_type: 'double', decimal_digits: 2, is_mandatory: true },
      { column_name: 'transfer_date', data_type: 'varchar', max_length: 30, is_mandatory: true },
      { column_name: 'notes', data_type: 'text', max_length: 10000, is_mandatory: false }
    ]
  },
  {
    table_name: 'transactions',
    columns: [
      { column_name: 'transaction_ref', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'transaction_date', data_type: 'varchar', max_length: 30, is_mandatory: true },
      { column_name: 'transaction_type', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'amount', data_type: 'double', decimal_digits: 2, is_mandatory: true },
      { column_name: 'account_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'account_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'person_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'person_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'category', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'related_ref', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'description', data_type: 'text', max_length: 10000, is_mandatory: false },
      { column_name: 'notes', data_type: 'text', max_length: 10000, is_mandatory: false }
    ]
  },
  {
    table_name: 'reminders',
    columns: [
      { column_name: 'reminder_type', data_type: 'varchar', max_length: 50, is_mandatory: true },
      { column_name: 'related_loan_id', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'related_ref', data_type: 'varchar', max_length: 50, is_mandatory: false },
      { column_name: 'person_name', data_type: 'varchar', max_length: 100, is_mandatory: false },
      { column_name: 'amount', data_type: 'double', decimal_digits: 2, is_mandatory: false },
      { column_name: 'due_date', data_type: 'varchar', max_length: 30, is_mandatory: true },
      { column_name: 'status', data_type: 'varchar', max_length: 20, is_mandatory: false },
      { column_name: 'notes', data_type: 'text', max_length: 10000, is_mandatory: false }
    ]
  },
  {
    table_name: 'app_settings',
    columns: [
      { column_name: 'setting_key', data_type: 'varchar', max_length: 100, is_mandatory: true },
      { column_name: 'setting_value', data_type: 'text', max_length: 10000, is_mandatory: false }
    ]
  }
];

const sleep = (ms) => new Promise(res => setTimeout(res, ms));

async function createAllTables() {
  const dec = Credential.crypt.decrypt(config.get('in.credential'));
  const token = dec.access_token;
  console.log('Connecting to Zoho Catalyst for project:', projectId);

  // 1. Fetch existing tables
  const listRes = await fetch(`https://api.catalyst.zoho.in/baas/v1/project/${projectId}/table`, {
    headers: {
      'Authorization': `Zoho-oauthtoken ${token}`,
      'Accept': 'application/vnd.catalyst.v2+json',
      'X-CATALYST-Environment': 'Development'
    }
  });
  const existingData = await listRes.json();
  const existingTables = (existingData.data || []).reduce((acc, t) => {
    acc[t.table_name] = t.table_id;
    return acc;
  }, {});
  console.log('Existing tables in Catalyst:', Object.keys(existingTables));

  for (const tableDef of tablesDefinition) {
    let tableId = existingTables[tableDef.table_name];
    if (!tableId) {
      console.log(`Creating table: ${tableDef.table_name}...`);
      const createRes = await fetch(`https://api.catalyst.zoho.in/baas/v1/project/${projectId}/table`, {
        method: 'POST',
        headers: {
          'Authorization': `Zoho-oauthtoken ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/vnd.catalyst.v2+json',
          'X-CATALYST-Environment': 'Development'
        },
        body: JSON.stringify({ table_name: tableDef.table_name })
      });
      const resJson = await createRes.json();
      if (createRes.status !== 200) {
        console.error(`Failed to create table ${tableDef.table_name}:`, resJson);
        continue;
      }
      tableId = resJson.data.table_id;
      console.log(`Table ${tableDef.table_name} created successfully (id: ${tableId})`);
      await sleep(2000);
    }

    // Now get existing columns for this table
    const colListRes = await fetch(`https://api.catalyst.zoho.in/baas/v1/project/${projectId}/table/${tableId}/column`, {
      headers: {
        'Authorization': `Zoho-oauthtoken ${token}`,
        'Accept': 'application/vnd.catalyst.v2+json',
        'X-CATALYST-Environment': 'Development'
      }
    });
    const colListData = await colListRes.json();
    const existingCols = new Set((colListData.data || []).map(c => c.column_name.toLowerCase()));

    // Filter columns that need to be added
    const colsToAdd = tableDef.columns.filter(c => !existingCols.has(c.column_name.toLowerCase()));

    if (colsToAdd.length > 0) {
      console.log(`Adding ${colsToAdd.length} columns to ${tableDef.table_name}...`);
      await sleep(1500);
      const colAddRes = await fetch(`https://api.catalyst.zoho.in/baas/v1/project/${projectId}/table/${tableId}/column`, {
        method: 'POST',
        headers: {
          'Authorization': `Zoho-oauthtoken ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/vnd.catalyst.v2+json',
          'X-CATALYST-Environment': 'Development'
        },
        body: JSON.stringify(colsToAdd)
      });
      const colAddJson = await colAddRes.json();
      if (colAddRes.status === 200) {
        console.log(`✓ Columns added successfully to ${tableDef.table_name}`);
      } else {
        console.error(`✗ Failed to add columns to ${tableDef.table_name}:`, colAddJson);
      }
    } else {
      console.log(`✓ All columns already exist for ${tableDef.table_name}`);
    }
  }

  console.log('Catalyst Data Store setup verified!');
}

createAllTables().catch(console.error);
