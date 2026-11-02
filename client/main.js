/**
 * Wallet Note — Fullstack Client Application Logic
 * Integrates all modules FR-01 through FR-13 with Zoho Catalyst Backend
 */

let API_BASE = '/api';

// Global State
let currentTheme = localStorage.getItem('wallet_note_theme') || 'light';
let appSettings = { currency_symbol: '₹', currency_code: 'INR' };
let globalAccounts = [];
let globalCategories = [];
let globalPeople = [];
let chartMonthlyTrends = null;
let chartCategoryBreakdown = null;

// Helper to extract clean error message from any backend response
function getErrorMessage(json, defaultMsg = 'An error occurred') {
  if (!json) return defaultMsg;
  if (typeof json === 'string') return json;
  if (json.message && typeof json.message === 'string') return json.message;
  if (json.data) {
    if (typeof json.data === 'string') return json.data;
    if (json.data.message && typeof json.data.message === 'string') return json.data.message;
  }
  if (json.error) {
    if (typeof json.error === 'string') return json.error;
    if (json.error.message && typeof json.error.message === 'string') return json.error.message;
    try { return JSON.stringify(json.error); } catch (_) {}
  }
  if (json.msg && typeof json.msg === 'string') return json.msg;
  if (json.description && typeof json.description === 'string') return json.description;
  return defaultMsg;
}

// Auto-detect whether we are running inside Catalyst router, Slate, or standalone Flask
async function initApiBase() {
  const CLOUD_FUNCTION_URL = 'https://wallet-note-60072054003.development.catalystserverless.in/server/wallet_note_function/api';

  // 1. If running on Catalyst Slate (onslate.in)
  if (window.location.hostname.includes('onslate.in')) {
    API_BASE = CLOUD_FUNCTION_URL;
    console.log('[Wallet Note] Running on Catalyst Slate, connected to Cloud Function:', API_BASE);
    return;
  }

  // 2. Local Catalyst Router (e.g. catalyst serve on port 3000)
  try {
    const res = await fetch('/server/wallet_note_function/api/ping');
    if (res.ok) {
      API_BASE = '/server/wallet_note_function/api';
      console.log('[Wallet Note] Connected via Catalyst Function Route:', API_BASE);
      return;
    }
  } catch (e) {}

  // 3. Direct route (standalone Flask / AppSail)
  try {
    const res2 = await fetch('/api/ping');
    if (res2.ok) {
      API_BASE = '/api';
      console.log('[Wallet Note] Connected via Direct Route:', API_BASE);
      return;
    }
  } catch (e) {}

  // 4. Fallback: if remote domain, use cloud function endpoint, else relative /api
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    API_BASE = CLOUD_FUNCTION_URL;
  } else {
    API_BASE = '/api';
  }
}

// Initialize on DOM Ready or immediately if DOM is already ready
async function startApp() {
  initTheme();
  initNavigation();
  initDropdown();
  initModals();
  lucide.createIcons();
  
  // Detect API route first
  await initApiBase();

  // Initial data load
  await loadInitialData();
  DashboardModule.load();
  RemindersModule.checkCount();

  // Sync button listener
  document.getElementById('btn-sync-catalyst')?.addEventListener('click', () => {
    triggerCatalystSync();
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startApp);
} else {
  startApp();
}

// Toast notification helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const msgStr = (message !== undefined && message !== null && String(message).trim() !== '' && String(message) !== 'undefined')
    ? String(message)
    : (type === 'error' ? 'An unexpected error occurred' : 'Notice');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info'}"></i>
    <span>${msgStr}</span>
  `;
  container.appendChild(toast);
  lucide.createIcons();
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Format currency
function formatCurrency(amount) {
  const symbol = appSettings.currency_symbol || '₹';
  const val = parseFloat(amount || 0);
  return `${symbol}${val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Theme handling
function applyTheme(theme) {
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('wallet_note_theme', theme);

  // Update theme toggle icon in topbar
  const toggleBtn = document.getElementById('btn-theme-toggle');
  if (toggleBtn) {
    toggleBtn.innerHTML = `<i data-lucide="${theme === 'dark' ? 'sun' : 'moon'}" id="theme-icon"></i>`;
    toggleBtn.title = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
    lucide.createIcons();
  }

  // Update settings dropdown if on screen
  const settingSelect = document.getElementById('setting-theme');
  if (settingSelect && settingSelect.value !== theme) {
    settingSelect.value = theme;
  }

  // Reload charts with theme-appropriate colors if charts exist
  if (chartMonthlyTrends || chartCategoryBreakdown) {
    DashboardModule.load();
  }
}

function initTheme() {
  // Apply saved or default theme
  applyTheme(currentTheme);

  // Set up click listener ONCE
  const toggleBtn = document.getElementById('btn-theme-toggle');
  if (toggleBtn && !toggleBtn._hasThemeListener) {
    toggleBtn._hasThemeListener = true;
    toggleBtn.addEventListener('click', () => {
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      applyTheme(newTheme);
      showToast(`Switched to ${newTheme === 'dark' ? 'Dark' : 'Light'} Mode`, 'info');
    });
  }
}

// Navigation & View Routing
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetView = item.getAttribute('data-view');
      navigate(targetView);
    });
  });

  // Mobile menu toggle
  document.getElementById('mobile-toggle')?.addEventListener('click', () => {
    document.getElementById('sidebar')?.classList.toggle('mobile-open');
  });
}

function navigate(viewName, param = null) {
  // Hide all views
  document.querySelectorAll('.page-view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const viewEl = document.getElementById(`view-${viewName}`);
  const navEl = document.querySelector(`.nav-item[data-view="${viewName}"]`);

  if (viewEl) {
    viewEl.classList.add('active');
  }
  if (navEl) {
    navEl.classList.add('active');
  }

  // Update Topbar Title
  const titles = {
    dashboard: 'Consolidated Dashboard',
    incomes: 'Income Management',
    expenses: 'Expense Management',
    borrowings: 'Borrowed Money Management',
    lendings: 'Lent Money Management',
    people: 'People Directory',
    ledger: 'Person-wise Personal Ledger',
    transactions: 'Unified Transaction Register',
    accounts: 'Account & Banking Management',
    reminders: 'Reminders & Due Dates',
    reports: 'Financial Reports & Analytics',
    settings: 'System Settings & Preferences'
  };
  document.getElementById('current-page-title').textContent = titles[viewName] || 'Wallet Note';

  // Close mobile sidebar if open
  document.getElementById('sidebar')?.classList.remove('mobile-open');

  // Trigger view specific loaders
  switch (viewName) {
    case 'dashboard': DashboardModule.load(); break;
    case 'incomes': IncomeModule.load(); break;
    case 'expenses': ExpenseModule.load(); break;
    case 'borrowings': BorrowModule.load(); break;
    case 'lendings': LendModule.load(); break;
    case 'people': PeopleModule.load(); break;
    case 'ledger': LedgerModule.load(param); break;
    case 'transactions': TransactionModule.load(); break;
    case 'accounts': AccountModule.load(); break;
    case 'reminders': RemindersModule.load(); break;
    case 'reports': ReportModule.load(); break;
    case 'settings': SettingsModule.load(); break;
  }
}

// Quick Add Dropdown Menu
function initDropdown() {
  const btn = document.getElementById('btn-quick-menu');
  const dropdown = document.getElementById('quick-dropdown');
  btn?.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown?.classList.toggle('show');
  });
  document.addEventListener('click', () => dropdown?.classList.remove('show'));
}

// Modals Handling
function initModals() {
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('open');
      }
    });
  });
}

function openModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) {
    if (modalId === 'modal-borrow' || modalId === 'modal-lend') {
      populatePeopleDropdowns();
    }
    const today = new Date().toISOString().split('T')[0];
    el.querySelectorAll('input[type="date"]').forEach(inp => {
      if (!inp.value) inp.value = today;
    });
    el.classList.add('open');
    lucide.createIcons();
  }
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) {
    el.classList.remove('open');
  }
  if (modalId === 'modal-person' && activePersonTarget) {
    if (activePersonTarget === 'lend') {
      const s = document.getElementById('form-lend-person');
      if (s && s.value === '__ADD_NEW__') s.value = '';
    } else if (activePersonTarget === 'borrow') {
      const s = document.getElementById('form-borrow-person');
      if (s && s.value === '__ADD_NEW__') s.value = '';
    } else if (activePersonTarget === 'ledger') {
      const s = document.getElementById('ledger-person-picker');
      if (s && s.value === '__ADD_NEW__') s.value = '';
    }
    activePersonTarget = null;
  }
}

// Initial Data: Accounts, Categories, Settings, People
async function loadInitialData() {
  try {
    const [accRes, catRes, setRes, pplRes] = await Promise.all([
      fetch(`${API_BASE}/accounts`).then(r => r.json()).catch(() => ({ status: 'error' })),
      fetch(`${API_BASE}/categories`).then(r => r.json()).catch(() => ({ status: 'error' })),
      fetch(`${API_BASE}/settings`).then(r => r.json()).catch(() => ({ status: 'error' })),
      fetch(`${API_BASE}/people`).then(r => r.json()).catch(() => ({ status: 'error' }))
    ]);

    if (accRes.status === 'success') {
      globalAccounts = accRes.data;
      populateAccountDropdowns();
    }
    if (catRes.status === 'success') {
      globalCategories = catRes.data;
      populateCategoryDropdowns();
    }
    if (setRes.status === 'success') {
      appSettings = setRes.data;
    }
    if (pplRes.status === 'success') {
      globalPeople = pplRes.data;
      populatePeopleDatalist();
    }
  } catch (err) {
    console.error('Error loading initial data:', err);
  }
}

function populateAccountDropdowns() {
  const dropdowns = [
    'income-account-filter', 'expense-account-filter', 'txn-account-filter',
    'form-income-account', 'form-expense-account', 'form-borrow-account',
    'form-lend-account', 'form-repay-account', 'form-collect-account',
    'form-transfer-from', 'form-transfer-to'
  ];

  dropdowns.forEach(id => {
    const select = document.getElementById(id);
    if (!select) return;
    const isFilter = id.includes('filter');
    select.innerHTML = isFilter ? '<option value="">All Accounts</option>' : '';
    globalAccounts.forEach(acc => {
      const opt = document.createElement('option');
      opt.value = acc.ROWID;
      opt.textContent = `${acc.account_name} (${formatCurrency(acc.current_balance)})`;
      select.appendChild(opt);
    });
  });
}

function populateCategoryDropdowns() {
  const expSelect = document.getElementById('form-expense-category');
  const expFilter = document.getElementById('expense-category-filter');
  const incSelect = document.getElementById('form-income-source');

  if (expSelect) {
    expSelect.innerHTML = '';
    globalCategories.filter(c => c.category_type === 'Expense').forEach(c => {
      expSelect.innerHTML += `<option value="${c.category_name}">${c.category_name}</option>`;
    });
  }
  if (expFilter) {
    expFilter.innerHTML = '<option value="">All Categories</option>';
    globalCategories.filter(c => c.category_type === 'Expense').forEach(c => {
      expFilter.innerHTML += `<option value="${c.category_name}">${c.category_name}</option>`;
    });
  }
  if (incSelect) {
    incSelect.innerHTML = '';
    globalCategories.filter(c => c.category_type === 'Income').forEach(c => {
      incSelect.innerHTML += `<option value="${c.category_name}">${c.category_name}</option>`;
    });
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

let activePersonTarget = null; // 'lend' | 'borrow' | 'ledger' | null

function populatePeopleDropdowns() {
  const datalist = document.getElementById('people-datalist');
  const picker = document.getElementById('ledger-person-picker');
  const lendPerson = document.getElementById('form-lend-person');
  const borrowPerson = document.getElementById('form-borrow-person');

  const buildPersonOptions = (label) => {
    let html = `<option value="">-- ${label} --</option>`;
    html += `<option value="__ADD_NEW__" style="color:var(--primary); font-weight:700;">➕ + Add New Person...</option>`;
    if (globalPeople && globalPeople.length > 0) {
      html += `<option disabled>────────────────────────────</option>`;
      globalPeople.forEach(p => {
        const mobLabel = p.mobile_number ? ` (${escapeHtml(p.mobile_number)})` : '';
        html += `<option value="${escapeHtml(p.full_name)}" data-mobile="${escapeHtml(p.mobile_number || '')}">${escapeHtml(p.full_name)}${mobLabel}</option>`;
      });
    }
    return html;
  };

  if (lendPerson) {
    const prev = lendPerson.value;
    lendPerson.innerHTML = buildPersonOptions('Select Borrower');
    if (prev && prev !== '__ADD_NEW__') {
      lendPerson.value = prev;
    }
  }

  if (borrowPerson) {
    const prev = borrowPerson.value;
    borrowPerson.innerHTML = buildPersonOptions('Select Lender');
    if (prev && prev !== '__ADD_NEW__') {
      borrowPerson.value = prev;
    }
  }

  if (datalist) {
    datalist.innerHTML = (globalPeople || []).map(p => `<option value="${escapeHtml(p.full_name)}"></option>`).join('');
  }

  if (picker) {
    const prev = picker.value;
    let html = '<option value="">Select a person...</option>';
    html += '<option value="__ADD_NEW__" style="color:var(--primary); font-weight:700;">➕ + Add New Person...</option>';
    if (globalPeople && globalPeople.length > 0) {
      html += '<option disabled>────────────────────────────</option>';
      globalPeople.forEach(p => {
        html += `<option value="${p.ROWID}">${escapeHtml(p.full_name)}</option>`;
      });
    }
    picker.innerHTML = html;
    if (prev && prev !== '__ADD_NEW__') picker.value = prev;
  }
}

function populatePeopleDatalist() {
  populatePeopleDropdowns();
}

function openAddPersonForLoan(targetType) {
  activePersonTarget = targetType;
  document.getElementById('form-person').reset();
  document.getElementById('person-id').value = '';
  document.getElementById('modal-person-title').textContent = 
    targetType === 'lend' ? 'Add New Borrower' : 
    (targetType === 'borrow' ? 'Add New Lender' : 'Add Person to Directory');
  openModal('modal-person');
}

function onPersonDropdownChange(selectEl, targetType) {
  const val = selectEl.value;

  if (val === '__ADD_NEW__') {
    openAddPersonForLoan(targetType);
    return;
  }

  const mobileInputId = targetType === 'lend' ? 'form-lend-mobile' : 'form-borrow-mobile';
  const mobileInput = document.getElementById(mobileInputId);
  if (mobileInput) {
    if (val) {
      const opt = selectEl.options[selectEl.selectedIndex];
      const mob = opt?.getAttribute('data-mobile') || '';
      mobileInput.value = mob;
    } else {
      mobileInput.value = '';
    }
  }
}

// Zoho Catalyst Sync Trigger
async function triggerCatalystSync() {
  showToast('Synchronizing with Zoho Catalyst Data Store...', 'info');
  try {
    const res = await fetch(`${API_BASE}/sync/catalyst`, { method: 'POST' });
    const json = await res.json();
    if (json.status === 'success') {
      showToast('Successfully synchronized with Zoho Catalyst!', 'success');
      await loadInitialData();
      DashboardModule.load();
    } else {
      showToast(getErrorMessage(json, 'Sync failed'), 'error');
    }
  } catch (e) {
    showToast('Failed to connect to Catalyst: ' + e.message, 'error');
  }
}

// -------------------------------------------------------------
// MODULE 1: DASHBOARD (FR-01)
// -------------------------------------------------------------
const DashboardModule = {
  async load() {
    const filter = document.getElementById('dash-date-filter')?.value || 'this_month';
    let startDate = '', endDate = '';
    const now = new Date();

    if (filter === 'this_month') {
      startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
      endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];
    } else if (filter === 'last_month') {
      startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1).toISOString().split('T')[0];
      endDate = new Date(now.getFullYear(), now.getMonth(), 0).toISOString().split('T')[0];
    } else if (filter === 'this_year') {
      startDate = `${now.getFullYear()}-01-01`;
      endDate = `${now.getFullYear()}-12-31`;
    }

    try {
      const res = await fetch(`${API_BASE}/dashboard?start_date=${startDate}&end_date=${endDate}`);
      const json = await res.json();
      if (json.status !== 'success') return;
      const d = json.data;

      // Update KPI Cards
      document.getElementById('dash-total-income').textContent = formatCurrency(d.metrics.total_income);
      document.getElementById('dash-total-expense').textContent = formatCurrency(d.metrics.total_expense);
      
      const netEl = document.getElementById('dash-net-income');
      netEl.textContent = formatCurrency(d.metrics.net_income);
      netEl.className = 'kpi-value ' + (d.metrics.net_income >= 0 ? 'amt-positive' : 'amt-negative');

      document.getElementById('dash-available-balance').textContent = formatCurrency(d.metrics.available_balance);
      document.getElementById('dash-outstanding-payables').textContent = formatCurrency(d.metrics.outstanding_payables);
      document.getElementById('dash-borrowed-subtext').textContent = `Borrowed: ${formatCurrency(d.metrics.total_borrowed)} | Repaid: ${formatCurrency(d.metrics.total_repaid)}`;

      document.getElementById('dash-outstanding-receivables').textContent = formatCurrency(d.metrics.outstanding_receivables);
      document.getElementById('dash-lent-subtext').textContent = `Lent: ${formatCurrency(d.metrics.total_lent)} | Collected: ${formatCurrency(d.metrics.total_collected)}`;

      // Render Charts
      DashboardModule.renderMonthlyChart(d.monthly_trends);
      DashboardModule.renderCategoryChart(d.category_breakdown);

      // Render Pending Obligations
      DashboardModule.renderPendingTable(d.pending_repayments, d.pending_collections);

      // Render Recent Transactions
      DashboardModule.renderRecentTxns(d.recent_transactions);

      // Reminders Bell Count
      const alertCount = d.overdue_summary.overdue_count + d.upcoming_summary.upcoming_count;
      const badge = document.getElementById('topbar-notif-count');
      if (badge) {
        badge.textContent = alertCount;
        badge.style.display = alertCount > 0 ? 'inline-block' : 'none';
      }

    } catch (e) {
      console.error('Error loading dashboard:', e);
    }
  },

  renderMonthlyChart(trends) {
    const ctx = document.getElementById('chart-monthly-trends');
    if (!ctx) return;
    if (chartMonthlyTrends) chartMonthlyTrends.destroy();

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    chartMonthlyTrends = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: trends.labels,
        datasets: [
          {
            label: 'Income',
            data: trends.income,
            backgroundColor: '#10b981',
            borderRadius: 6
          },
          {
            label: 'Expense',
            data: trends.expense,
            backgroundColor: '#ef4444',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: textColor } }
        },
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: textColor } },
          y: { grid: { color: gridColor }, ticks: { color: textColor } }
        }
      }
    });
  },

  renderCategoryChart(cats) {
    const ctx = document.getElementById('chart-category-breakdown');
    if (!ctx) return;
    if (chartCategoryBreakdown) chartCategoryBreakdown.destroy();

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    if (!cats || cats.length === 0) {
      chartCategoryBreakdown = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['No Expenses Recorded'],
          datasets: [{ data: [1], backgroundColor: ['#94a3b8'] }]
        },
        options: { responsive: true, plugins: { legend: { labels: { color: textColor } } } }
      });
      return;
    }

    const colors = ['#ef4444', '#f97316', '#eab308', '#10b981', '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899', '#64748b'];
    chartCategoryBreakdown = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: cats.map(c => c.category),
        datasets: [{
          data: cats.map(c => c.total),
          backgroundColor: colors.slice(0, cats.length),
          borderWidth: 2,
          borderColor: isDark ? '#131c2e' : '#ffffff'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { color: textColor, boxWidth: 12 } }
        }
      }
    });
  },

  renderPendingTable(repayments, collections) {
    const tbody = document.getElementById('dash-pending-table-body');
    if (!tbody) return;
    const combined = [];

    (repayments || []).forEach(r => combined.push({ ...r, obligationType: 'Payable' }));
    (collections || []).forEach(c => combined.push({ ...c, obligationType: 'Receivable' }));

    if (combined.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:20px;">No pending repayments or collections. All obligations clear!</td></tr>';
      return;
    }

    tbody.innerHTML = combined.map(item => {
      const isPayable = item.obligationType === 'Payable';
      const remaining = isPayable ? item.outstanding_payable : item.outstanding_receivable;
      const dueDate = isPayable ? item.due_date : item.expected_return_date;
      const statusBadge = `<span class="badge badge-${item.status.toLowerCase().replace(' ', '')}">${item.status}</span>`;
      
      const actionBtn = isPayable 
        ? `<button class="btn-primary btn-sm" onclick="BorrowModule.openRepayModal('${item.ROWID}', '${item.person_name}', ${remaining})">Repay</button>`
        : `<button class="btn-primary btn-sm" style="background-color:var(--info);" onclick="LendModule.openCollectModal('${item.ROWID}', '${item.person_name}', ${remaining})">Collect</button>`;

      return `
        <tr>
          <td><span class="badge ${isPayable ? 'badge-pending' : 'badge-partially'}">${item.obligationType}</span></td>
          <td><strong>${item.person_name}</strong></td>
          <td class="${isPayable ? 'amt-negative' : 'amt-positive'}">${formatCurrency(remaining)}</td>
          <td>${dueDate || 'Not specified'}</td>
          <td>${statusBadge}</td>
          <td>${actionBtn}</td>
        </tr>
      `;
    }).join('');
  },

  renderRecentTxns(txns) {
    const tbody = document.getElementById('dash-recent-txns-body');
    if (!tbody) return;
    if (!txns || txns.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:20px;">No recent transactions.</td></tr>';
      return;
    }

    tbody.innerHTML = txns.map(t => {
      const isPositive = ['Income', 'Loan Collection'].includes(t.transaction_type);
      const isNegative = ['Expense', 'Loan Repayment'].includes(t.transaction_type);
      const amtClass = isPositive ? 'amt-positive' : isNegative ? 'amt-negative' : 'amt-neutral';
      const sign = isPositive ? '+' : isNegative ? '-' : '';

      return `
        <tr>
          <td>${t.transaction_date}</td>
          <td><span class="badge ${isPositive ? 'badge-completed' : isNegative ? 'badge-overdue' : 'badge-partially'}">${t.transaction_type}</span></td>
          <td><div style="font-weight:500;">${t.description}</div><small style="color:var(--text-muted);">${t.account_name || ''}</small></td>
          <td class="${amtClass}">${sign}${formatCurrency(t.amount)}</td>
        </tr>
      `;
    }).join('');
  }
};

// -------------------------------------------------------------
// MODULE 2: INCOMES (FR-02)
// -------------------------------------------------------------
const IncomeModule = {
  async load() {
    const search = document.getElementById('income-search')?.value || '';
    const account_id = document.getElementById('income-account-filter')?.value || '';
    const start_date = document.getElementById('income-start-date')?.value || '';
    const end_date = document.getElementById('income-end-date')?.value || '';

    const params = new URLSearchParams({ search, account_id, start_date, end_date });
    try {
      const res = await fetch(`${API_BASE}/incomes?${params}`);
      const json = await res.json();
      const tbody = document.getElementById('incomes-table-body');
      if (!tbody) return;

      if (!json.data || json.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--text-muted);">No income records found. Click "+ Record Income" to add.</td></tr>';
        return;
      }

      tbody.innerHTML = json.data.map(i => `
        <tr>
          <td><code>${i.income_ref}</code></td>
          <td>${i.transaction_date}</td>
          <td><strong>${i.source}</strong></td>
          <td>${i.received_from || '-'}</td>
          <td>${i.account_name}</td>
          <td>${i.payment_method || '-'}</td>
          <td class="amt-positive">+${formatCurrency(i.amount)}</td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="btn-secondary btn-sm" onclick="IncomeModule.edit('${i.ROWID}')"><i data-lucide="edit-2"></i></button>
              <button class="btn-secondary btn-sm" style="color:var(--danger);" onclick="IncomeModule.delete('${i.ROWID}')"><i data-lucide="trash-2"></i></button>
            </div>
          </td>
        </tr>
      `).join('');
      lucide.createIcons();
    } catch (e) {
      console.error(e);
    }
  },

  async save(e) {
    e.preventDefault();
    const id = document.getElementById('income-id').value;
    const payload = {
      amount: document.getElementById('form-income-amount').value,
      transaction_date: document.getElementById('form-income-date').value,
      source: document.getElementById('form-income-source').value,
      account_id: document.getElementById('form-income-account').value,
      received_from: document.getElementById('form-income-payer').value,
      payment_method: document.getElementById('form-income-method').value,
      description: document.getElementById('form-income-desc').value
    };

    const url = id ? `${API_BASE}/incomes/${id}` : `${API_BASE}/incomes`;
    const method = id ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast(id ? 'Income updated successfully' : 'Income recorded successfully', 'success');
        closeModal('modal-income');
        document.getElementById('form-income').reset();
        document.getElementById('income-id').value = '';
        IncomeModule.load();
        DashboardModule.load();
        loadInitialData();
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error saving income: ' + err.message, 'error');
    }
  },

  async edit(id) {
    try {
      const res = await fetch(`${API_BASE}/incomes/${id}`);
      const json = await res.json();
      if (json.status === 'success') {
        const d = json.data;
        document.getElementById('income-id').value = d.ROWID;
        document.getElementById('form-income-amount').value = d.amount;
        document.getElementById('form-income-date').value = d.transaction_date;
        document.getElementById('form-income-source').value = d.source;
        document.getElementById('form-income-account').value = d.account_id;
        document.getElementById('form-income-payer').value = d.received_from || '';
        document.getElementById('form-income-method').value = d.payment_method || 'Bank Transfer';
        document.getElementById('form-income-desc').value = d.description || '';
        document.getElementById('modal-income-title').textContent = 'Edit Income Record';
        openModal('modal-income');
      }
    } catch (e) {
      showToast('Error fetching income: ' + e.message, 'error');
    }
  },

  async delete(id) {
    if (!confirm('Are you sure you want to delete this income record? Account balance will be recalculated.')) return;
    try {
      const res = await fetch(`${API_BASE}/incomes/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Income deleted successfully', 'success');
        IncomeModule.load();
        DashboardModule.load();
        loadInitialData();
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (e) {
      showToast('Error deleting income: ' + e.message, 'error');
    }
  }
};

// -------------------------------------------------------------
// MODULE 3: EXPENSES (FR-03)
// -------------------------------------------------------------
const ExpenseModule = {
  async load() {
    const search = document.getElementById('expense-search')?.value || '';
    const category = document.getElementById('expense-category-filter')?.value || '';
    const account_id = document.getElementById('expense-account-filter')?.value || '';
    const start_date = document.getElementById('expense-start-date')?.value || '';
    const end_date = document.getElementById('expense-end-date')?.value || '';

    const params = new URLSearchParams({ search, category, account_id, start_date, end_date });
    try {
      const res = await fetch(`${API_BASE}/expenses?${params}`);
      const json = await res.json();
      const tbody = document.getElementById('expenses-table-body');
      if (!tbody) return;

      if (!json.data || json.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--text-muted);">No expense records found. Click "+ Record Expense" to add.</td></tr>';
        return;
      }

      tbody.innerHTML = json.data.map(e => `
        <tr>
          <td><code>${e.expense_ref}</code></td>
          <td>${e.transaction_date}</td>
          <td><strong>${e.category}</strong></td>
          <td>${e.paid_to || '-'}</td>
          <td>${e.account_name}</td>
          <td>${e.payment_method || '-'}</td>
          <td class="amt-negative">-${formatCurrency(e.amount)}</td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="btn-secondary btn-sm" onclick="ExpenseModule.edit('${e.ROWID}')"><i data-lucide="edit-2"></i></button>
              <button class="btn-secondary btn-sm" style="color:var(--danger);" onclick="ExpenseModule.delete('${e.ROWID}')"><i data-lucide="trash-2"></i></button>
            </div>
          </td>
        </tr>
      `).join('');
      lucide.createIcons();
    } catch (e) {
      console.error(e);
    }
  },

  async save(e) {
    e.preventDefault();
    const id = document.getElementById('expense-id').value;
    const payload = {
      amount: document.getElementById('form-expense-amount').value,
      transaction_date: document.getElementById('form-expense-date').value,
      category: document.getElementById('form-expense-category').value,
      account_id: document.getElementById('form-expense-account').value,
      paid_to: document.getElementById('form-expense-payee').value,
      payment_method: document.getElementById('form-expense-method').value,
      description: document.getElementById('form-expense-desc').value
    };

    const url = id ? `${API_BASE}/expenses/${id}` : `${API_BASE}/expenses`;
    const method = id ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast(id ? 'Expense updated successfully' : 'Expense recorded successfully', 'success');
        closeModal('modal-expense');
        document.getElementById('form-expense').reset();
        document.getElementById('expense-id').value = '';
        ExpenseModule.load();
        DashboardModule.load();
        loadInitialData();
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error saving expense: ' + err.message, 'error');
    }
  },

  async edit(id) {
    try {
      const res = await fetch(`${API_BASE}/expenses/${id}`);
      const json = await res.json();
      if (json.status === 'success') {
        const d = json.data;
        document.getElementById('expense-id').value = d.ROWID;
        document.getElementById('form-expense-amount').value = d.amount;
        document.getElementById('form-expense-date').value = d.transaction_date;
        document.getElementById('form-expense-category').value = d.category;
        document.getElementById('form-expense-account').value = d.account_id;
        document.getElementById('form-expense-payee').value = d.paid_to || '';
        document.getElementById('form-expense-method').value = d.payment_method || 'UPI';
        document.getElementById('form-expense-desc').value = d.description || '';
        document.getElementById('modal-expense-title').textContent = 'Edit Expense Record';
        openModal('modal-expense');
      }
    } catch (e) {
      showToast('Error fetching expense: ' + e.message, 'error');
    }
  },

  async delete(id) {
    if (!confirm('Are you sure you want to delete this expense record? Account balance will be recalculated.')) return;
    try {
      const res = await fetch(`${API_BASE}/expenses/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Expense deleted successfully', 'success');
        ExpenseModule.load();
        DashboardModule.load();
        loadInitialData();
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (e) {
      showToast('Error deleting expense: ' + e.message, 'error');
    }
  }
};

// -------------------------------------------------------------
// NOTIFICATION & ADVICE MODULE (AUTOMATED SMS ENGINE)
// -------------------------------------------------------------
const NotificationModule = {
  activeNotificationData: null,

  showNotificationModal(smsData) {
    this.activeNotificationData = smsData;
    const el = document.getElementById('modal-notification-sent');
    if (!el) return;

    const recipientEl = document.getElementById('notif-modal-recipient');
    const msgEl = document.getElementById('notif-modal-message');
    const gatewayEl = document.getElementById('notif-modal-gateway-name');
    const smsLinkEl = document.getElementById('notif-modal-sms-link');
    const badgeEl = document.getElementById('notif-modal-status-badge');

    if (recipientEl) {
      const recipientStr = smsData.recipient_name 
        ? `${smsData.phone_number} (${smsData.recipient_name})` 
        : smsData.phone_number;
      recipientEl.textContent = `SMS Dispatched to: ${recipientStr}`;
    }
    if (msgEl) {
      msgEl.textContent = smsData.message_text || '';
    }
    if (gatewayEl) {
      gatewayEl.textContent = smsData.gateway || smsData.provider || 'Catalyst Automated SMS Engine';
    }
    if (badgeEl) {
      badgeEl.textContent = smsData.sms_sent ? 'SMS Dispatched' : 'Dispatched';
      badgeEl.className = 'badge badge-completed';
    }
    if (smsLinkEl) {
      smsLinkEl.href = `sms:${smsData.phone_number}?body=${encodeURIComponent(smsData.message_text || '')}`;
    }

    openModal('modal-notification-sent');
    showToast(`SMS sent to ${smsData.phone_number}`, 'success');
  },

  async copyNotificationText() {
    const text = document.getElementById('notif-modal-message')?.textContent || '';
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      showToast('SMS message copied to clipboard!', 'success');
    } catch (err) {
      showToast('Copied to clipboard', 'info');
    }
  },

  async resendActiveSms() {
    if (!this.activeNotificationData || !this.activeNotificationData.phone_number) {
      showToast('No active SMS to resend.', 'warning');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/notifications/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: this.activeNotificationData.phone_number,
          notification_type: this.activeNotificationData.notification_type || 'loan_given',
          details: {
            person_name: this.activeNotificationData.recipient_name || '',
            amount: this.activeNotificationData.amount || 0,
            reference: this.activeNotificationData.reference || 'RESEND',
            message: this.activeNotificationData.message_text || ''
          }
        })
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('SMS re-sent successfully!', 'success');
        this.showNotificationModal(json.data);
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (e) {
      showToast('Error resending SMS: ' + e.message, 'error');
    }
  },

  async sendLoanSms(loanType, loanId) {
    try {
      const url = loanType === 'lend' ? `${API_BASE}/lendings/${loanId}` : `${API_BASE}/borrowings/${loanId}`;
      const res = await fetch(url);
      const json = await res.json();
      if (json.status !== 'success' || !json.data) return;
      const d = json.data;
      const phone = d.mobile_number;
      if (!phone) {
        showToast('No contact phone number recorded for this loan.', 'warning');
        return;
      }

      const notifType = loanType === 'lend' ? 'loan_given' : 'loan_received';
      const sendRes = await fetch(`${API_BASE}/notifications/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: phone,
          notification_type: notifType,
          details: {
            loan_id: d.ROWID,
            person_name: d.person_name,
            amount: loanType === 'lend' ? d.lent_amount : d.borrowed_amount,
            reference: loanType === 'lend' ? d.lend_ref : d.borrow_ref,
            date: loanType === 'lend' ? d.lend_date : d.borrow_date,
            due_date: loanType === 'lend' ? d.expected_return_date : d.due_date,
            account_name: loanType === 'lend' ? d.disbursement_account_name : d.receiving_account_name,
            notes: d.notes || d.interest_info || ''
          }
        })
      });
      const sendJson = await sendRes.json();
      if (sendJson.status === 'success') {
        this.showNotificationModal(sendJson.data);
      } else {
        showToast(getErrorMessage(sendJson), 'error');
      }
    } catch (e) {
      showToast('Error dispatching SMS: ' + e.message, 'error');
    }
  },

  // Backwards compatibility alias
  openShareLoan(loanType, loanId) {
    return this.sendLoanSms(loanType, loanId);
  },

  async sendDueReminder(loanId, type) {
    try {
      const res = await fetch(`${API_BASE}/lendings/${loanId}`);
      const json = await res.json();
      if (json.status !== 'success' || !json.data) {
        showToast('Could not load loan details.', 'error');
        return;
      }
      const l = json.data;
      if (!l.mobile_number) {
        showToast(`No contact number recorded for ${l.person_name}.`, 'warning');
        return;
      }

      const sendRes = await fetch(`${API_BASE}/notifications/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: l.mobile_number,
          notification_type: 'reminder',
          details: {
            loan_id: l.ROWID,
            person_name: l.person_name,
            amount: l.outstanding_receivable,
            reference: l.lend_ref,
            due_date: l.expected_return_date
          }
        })
      });
      const sendJson = await sendRes.json();
      if (sendJson.status === 'success') {
        this.showNotificationModal(sendJson.data);
      } else {
        showToast(getErrorMessage(sendJson), 'error');
      }
    } catch (e) {
      showToast('Error sending SMS reminder: ' + e.message, 'error');
    }
  },

  async sendLedgerStatement() {
    const personId = document.getElementById('ledger-person-picker')?.value;
    if (!personId) {
      showToast('Please select a person first.', 'warning');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/people/${personId}/ledger`);
      const json = await res.json();
      if (json.status !== 'success') return;
      const d = json.data;
      const phone = d.person.mobile_number;
      if (!phone) {
        showToast(`No mobile number registered for ${d.person.full_name}.`, 'warning');
        return;
      }

      const sendRes = await fetch(`${API_BASE}/notifications/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: phone,
          notification_type: 'statement',
          details: {
            person_name: d.person.full_name,
            remaining_to_collect: d.summary.remaining_to_collect,
            remaining_to_pay: d.summary.remaining_to_pay,
            net_balance: d.summary.net_balance,
            date: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
          }
        })
      });
      const sendJson = await sendRes.json();
      if (sendJson.status === 'success') {
        this.showNotificationModal(sendJson.data);
      } else {
        showToast(getErrorMessage(sendJson), 'error');
      }
    } catch (e) {
      showToast('Error sending statement SMS: ' + e.message, 'error');
    }
  },

  async sendTestNotification() {
    const phone = prompt('Enter recipient mobile number to send test SMS (e.g. 9876543210):');
    if (!phone) return;
    try {
      const res = await fetch(`${API_BASE}/notifications/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: phone,
          notification_type: 'loan_given',
          details: {
            person_name: 'Valued Contact',
            amount: 5000.00,
            reference: 'TEST-SMS',
            date: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
            due_date: '30-Nov-2026',
            account_name: 'Cash Wallet',
            notes: 'Test SMS from Wallet Note'
          }
        })
      });
      const json = await res.json();
      if (json.status === 'success') {
        this.showNotificationModal(json.data);
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (e) {
      showToast('Test failed: ' + e.message, 'error');
    }
  }
};

// -------------------------------------------------------------
// MODULE 4: BORROWED MONEY MANAGEMENT (FR-04)
// -------------------------------------------------------------
const BorrowModule = {
  async load() {
    const status = document.getElementById('borrow-status-filter')?.value || '';
    try {
      const res = await fetch(`${API_BASE}/borrowings?status=${status}`);
      const json = await res.json();
      const tbody = document.getElementById('borrowings-table-body');
      if (!tbody) return;

      if (!json.data || json.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:24px; color:var(--text-muted);">No borrowed money records found. Click "+ New Borrowing" to record.</td></tr>';
        return;
      }

      tbody.innerHTML = json.data.map(b => {
        const badgeClass = `badge-${b.status.toLowerCase().replace(' ', '')}`;
        const canRepay = b.outstanding_payable > 0;

        return `
          <tr>
            <td><code>${b.borrow_ref}</code></td>
            <td><strong>${b.person_name}</strong><br><small style="color:var(--text-muted);">${b.mobile_number || ''}</small></td>
            <td>${b.borrow_date}</td>
            <td>${b.due_date || 'No due date'}</td>
            <td>${formatCurrency(b.borrowed_amount)}</td>
            <td class="amt-positive">${formatCurrency(b.total_repaid)}</td>
            <td class="amt-negative" style="font-weight:700;">${formatCurrency(b.outstanding_payable)}</td>
            <td><span class="badge ${badgeClass}">${b.status}</span></td>
            <td>
              <div style="display:flex; gap:6px;">
                ${canRepay ? `<button class="btn-primary btn-sm" onclick="BorrowModule.openRepayModal('${b.ROWID}', '${b.person_name}', ${b.outstanding_payable})">Repay</button>` : ''}
                <button class="btn-secondary btn-sm" style="color:var(--primary);" onclick="NotificationModule.sendLoanSms('borrow', '${b.ROWID}')" title="Send SMS Receipt to Lender"><i data-lucide="message-square"></i></button>
                <button class="btn-secondary btn-sm" onclick="navigate('ledger', '${b.person_id}')" title="View Person Ledger"><i data-lucide="book-open"></i></button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
      lucide.createIcons();
    } catch (e) {
      console.error(e);
    }
  },

  async save(e) {
    e.preventDefault();
    const personName = document.getElementById('form-borrow-person').value;
    if (!personName || personName === '__ADD_NEW__') {
      showToast('Please select or add a lender.', 'warning');
      return;
    }
    const payload = {
      person_name: personName,
      mobile_number: document.getElementById('form-borrow-mobile').value,
      send_notification: document.getElementById('form-borrow-notify')?.checked ?? true,
      borrowed_amount: document.getElementById('form-borrow-amount').value,
      receiving_account_id: document.getElementById('form-borrow-account').value,
      borrow_date: document.getElementById('form-borrow-date').value,
      due_date: document.getElementById('form-borrow-duedate').value,
      interest_info: document.getElementById('form-borrow-interest').value,
      notes: document.getElementById('form-borrow-notes').value
    };

    try {
      const res = await fetch(`${API_BASE}/borrowings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        closeModal('modal-borrow');
        document.getElementById('form-borrow').reset();
        BorrowModule.load();
        DashboardModule.load();
        loadInitialData();

        if (json.data && json.data.notification && json.data.notification.phone_number) {
          NotificationModule.showNotificationModal(json.data.notification);
        } else {
          showToast('Borrowed money recorded successfully! Funds added to account.', 'success');
        }
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error recording borrowing: ' + err.message, 'error');
    }
  },

  openRepayModal(borrowId, personName, outstanding) {
    document.getElementById('repay-borrow-id').value = borrowId;
    document.getElementById('repay-lender-name').textContent = personName;
    document.getElementById('repay-outstanding-amt').textContent = formatCurrency(outstanding);
    document.getElementById('form-repay-amount').value = outstanding;
    document.getElementById('form-repay-amount').max = outstanding;
    document.getElementById('form-repay-date').value = new Date().toISOString().split('T')[0];
    openModal('modal-repay');
  },

  async submitRepayment(e) {
    e.preventDefault();
    const borrowId = document.getElementById('repay-borrow-id').value;
    const payload = {
      amount: document.getElementById('form-repay-amount').value,
      payment_date: document.getElementById('form-repay-date').value,
      account_id: document.getElementById('form-repay-account').value,
      payment_method: document.getElementById('form-repay-method').value,
      notes: document.getElementById('form-repay-notes').value
    };

    try {
      const res = await fetch(`${API_BASE}/borrowings/${borrowId}/repay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        closeModal('modal-repay');
        document.getElementById('form-repay').reset();
        BorrowModule.load();
        DashboardModule.load();
        loadInitialData();

        if (document.getElementById('form-repay-notify')?.checked && json.data && json.data.notification && json.data.notification.phone_number) {
          NotificationModule.showNotificationModal(json.data.notification);
        } else {
          showToast('Repayment recorded! Loan balance updated.', 'success');
        }
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error posting repayment: ' + err.message, 'error');
    }
  }
};

// -------------------------------------------------------------
// MODULE 5: LENT MONEY MANAGEMENT (FR-05)
// -------------------------------------------------------------
const LendModule = {
  async load() {
    const status = document.getElementById('lend-status-filter')?.value || '';
    try {
      const res = await fetch(`${API_BASE}/lendings?status=${status}`);
      const json = await res.json();
      const tbody = document.getElementById('lendings-table-body');
      if (!tbody) return;

      if (!json.data || json.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:24px; color:var(--text-muted);">No lent money records found. Click "+ New Lending" to record.</td></tr>';
        return;
      }

      tbody.innerHTML = json.data.map(l => {
        const badgeClass = `badge-${l.status.toLowerCase().replace(' ', '')}`;
        const canCollect = l.outstanding_receivable > 0;

        return `
          <tr>
            <td><code>${l.lend_ref}</code></td>
            <td><strong>${l.person_name}</strong><br><small style="color:var(--text-muted);">${l.mobile_number || ''}</small></td>
            <td>${l.lend_date}</td>
            <td>${l.expected_return_date || 'No return date'}</td>
            <td>${formatCurrency(l.lent_amount)}</td>
            <td class="amt-positive">${formatCurrency(l.total_collected)}</td>
            <td class="amt-positive" style="font-weight:700;">${formatCurrency(l.outstanding_receivable)}</td>
            <td><span class="badge ${badgeClass}">${l.status}</span></td>
            <td>
              <div style="display:flex; gap:6px;">
                ${canCollect ? `<button class="btn-primary btn-sm" style="background-color:var(--info);" onclick="LendModule.openCollectModal('${l.ROWID}', '${l.person_name}', ${l.outstanding_receivable})">Collect</button>` : ''}
                <button class="btn-secondary btn-sm" style="color:var(--primary);" onclick="NotificationModule.sendLoanSms('lend', '${l.ROWID}')" title="Send SMS Advice to Borrower"><i data-lucide="message-square"></i></button>
                <button class="btn-secondary btn-sm" onclick="navigate('ledger', '${l.person_id}')" title="View Person Ledger"><i data-lucide="book-open"></i></button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
      lucide.createIcons();
    } catch (e) {
      console.error(e);
    }
  },

  async save(e) {
    e.preventDefault();
    const personName = document.getElementById('form-lend-person').value;
    if (!personName || personName === '__ADD_NEW__') {
      showToast('Please select or add a borrower.', 'warning');
      return;
    }
    const payload = {
      person_name: personName,
      mobile_number: document.getElementById('form-lend-mobile').value,
      send_notification: document.getElementById('form-lend-notify')?.checked ?? true,
      lent_amount: document.getElementById('form-lend-amount').value,
      disbursement_account_id: document.getElementById('form-lend-account').value,
      lend_date: document.getElementById('form-lend-date').value,
      expected_return_date: document.getElementById('form-lend-returndate').value,
      interest_info: document.getElementById('form-lend-interest').value,
      notes: document.getElementById('form-lend-notes').value
    };

    try {
      const res = await fetch(`${API_BASE}/lendings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        closeModal('modal-lend');
        document.getElementById('form-lend').reset();
        LendModule.load();
        DashboardModule.load();
        loadInitialData();

        if (json.data && json.data.notification && json.data.notification.phone_number) {
          NotificationModule.showNotificationModal(json.data.notification);
        } else {
          showToast('Lent money recorded! Account balance updated.', 'success');
        }
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error recording lending: ' + err.message, 'error');
    }
  },

  openCollectModal(lendId, personName, outstanding) {
    document.getElementById('collect-lend-id').value = lendId;
    document.getElementById('collect-borrower-name').textContent = personName;
    document.getElementById('collect-outstanding-amt').textContent = formatCurrency(outstanding);
    document.getElementById('form-collect-amount').value = outstanding;
    document.getElementById('form-collect-amount').max = outstanding;
    document.getElementById('form-collect-date').value = new Date().toISOString().split('T')[0];
    openModal('modal-collect');
  },

  async submitCollection(e) {
    e.preventDefault();
    const lendId = document.getElementById('collect-lend-id').value;
    const payload = {
      amount: document.getElementById('form-collect-amount').value,
      payment_date: document.getElementById('form-collect-date').value,
      account_id: document.getElementById('form-collect-account').value,
      payment_method: document.getElementById('form-collect-method').value,
      notes: document.getElementById('form-collect-notes').value
    };

    try {
      const res = await fetch(`${API_BASE}/lendings/${lendId}/collect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        closeModal('modal-collect');
        document.getElementById('form-collect').reset();
        LendModule.load();
        DashboardModule.load();
        loadInitialData();

        if (document.getElementById('form-collect-notify')?.checked && json.data && json.data.notification && json.data.notification.phone_number) {
          NotificationModule.showNotificationModal(json.data.notification);
        } else {
          showToast('Collection recorded! Funds deposited to account.', 'success');
        }
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error posting collection: ' + err.message, 'error');
    }
  }
};

// -------------------------------------------------------------
// MODULE 7: PEOPLE MANAGEMENT (FR-07)
// -------------------------------------------------------------
const PeopleModule = {
  async load() {
    const search = document.getElementById('people-search')?.value.toLowerCase() || '';
    try {
      const res = await fetch(`${API_BASE}/people`);
      const json = await res.json();
      const tbody = document.getElementById('people-table-body');
      if (!tbody) return;

      let people = json.data || [];
      if (search) {
        people = people.filter(p => p.full_name.toLowerCase().includes(search) || (p.mobile_number && p.mobile_number.includes(search)));
      }

      if (people.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:24px; color:var(--text-muted);">No people in directory. Click "+ Add Person" to add.</td></tr>';
        return;
      }

      tbody.innerHTML = people.map(p => {
        const net = p.net_balance || 0;
        const netClass = net > 0 ? 'amt-positive' : net < 0 ? 'amt-negative' : 'amt-neutral';
        const netText = net > 0 ? `Owes you ${formatCurrency(net)}` : net < 0 ? `You owe ${formatCurrency(Math.abs(net))}` : 'Settled';

        return `
          <tr>
            <td><strong>${p.full_name}</strong><br><small style="color:var(--text-muted);">${p.email || ''}</small></td>
            <td>${p.mobile_number || '-'}</td>
            <td>${formatCurrency(p.total_lent)}</td>
            <td class="amt-positive" style="font-weight:600;">${formatCurrency(p.remaining_to_collect)}</td>
            <td>${formatCurrency(p.total_borrowed)}</td>
            <td class="amt-negative" style="font-weight:600;">${formatCurrency(p.remaining_to_pay)}</td>
            <td><strong class="${netClass}">${netText}</strong></td>
            <td>
              <div style="display:flex; gap:6px;">
                <button class="btn-primary btn-sm" onclick="navigate('ledger', '${p.ROWID}')"><i data-lucide="book-open"></i> Ledger</button>
                <button class="btn-secondary btn-sm" onclick="PeopleModule.edit('${p.ROWID}')"><i data-lucide="edit-2"></i></button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
      lucide.createIcons();
    } catch (e) {
      console.error(e);
    }
  },

  async save(e) {
    e.preventDefault();
    const id = document.getElementById('person-id').value;
    const payload = {
      full_name: document.getElementById('form-person-name').value,
      mobile_number: document.getElementById('form-person-mobile').value,
      email: document.getElementById('form-person-email').value,
      address: document.getElementById('form-person-address').value,
      notes: document.getElementById('form-person-notes').value
    };

    const url = id ? `${API_BASE}/people/${id}` : `${API_BASE}/people`;
    const method = id ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        const savedPerson = json.data;
        showToast(id ? 'Person updated' : 'Person added to directory', 'success');
        closeModal('modal-person');
        document.getElementById('form-person').reset();
        document.getElementById('person-id').value = '';
        PeopleModule.load();
        await loadInitialData();

        if (activePersonTarget) {
          if (activePersonTarget === 'lend') {
            const selectEl = document.getElementById('form-lend-person');
            const mobileEl = document.getElementById('form-lend-mobile');
            if (selectEl && savedPerson) selectEl.value = savedPerson.full_name;
            if (mobileEl && savedPerson && savedPerson.mobile_number) mobileEl.value = savedPerson.mobile_number;
            showToast(`Selected "${savedPerson.full_name}" as borrower`, 'info');
          } else if (activePersonTarget === 'borrow') {
            const selectEl = document.getElementById('form-borrow-person');
            const mobileEl = document.getElementById('form-borrow-mobile');
            if (selectEl && savedPerson) selectEl.value = savedPerson.full_name;
            if (mobileEl && savedPerson && savedPerson.mobile_number) mobileEl.value = savedPerson.mobile_number;
            showToast(`Selected "${savedPerson.full_name}" as lender`, 'info');
          } else if (activePersonTarget === 'ledger') {
            const picker = document.getElementById('ledger-person-picker');
            if (picker && savedPerson) {
              picker.value = savedPerson.ROWID;
              LedgerModule.load(savedPerson.ROWID);
            }
          }
          activePersonTarget = null;
        }
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error saving person: ' + err.message, 'error');
    }
  },

  async edit(id) {
    try {
      const res = await fetch(`${API_BASE}/people/${id}`);
      const json = await res.json();
      if (json.status === 'success') {
        const d = json.data;
        document.getElementById('person-id').value = d.ROWID;
        document.getElementById('form-person-name').value = d.full_name;
        document.getElementById('form-person-mobile').value = d.mobile_number || '';
        document.getElementById('form-person-email').value = d.email || '';
        document.getElementById('form-person-address').value = d.address || '';
        document.getElementById('form-person-notes').value = d.notes || '';
        document.getElementById('modal-person-title').textContent = 'Edit Person Details';
        openModal('modal-person');
      }
    } catch (e) {
      showToast('Error fetching person: ' + e.message, 'error');
    }
  }
};

// -------------------------------------------------------------
// MODULE 8: PERSON-WISE PERSONAL LEDGER (FR-08)
// -------------------------------------------------------------
const LedgerModule = {
  async load(personId) {
    if (personId === '__ADD_NEW__') {
      openAddPersonForLoan('ledger');
      return;
    }
    if (!personId) {
      document.getElementById('ledger-hero-card').style.display = 'none';
      document.getElementById('ledger-activities-body').innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">Please select a person from the dropdown above.</td></tr>';
      return;
    }

    const picker = document.getElementById('ledger-person-picker');
    if (picker) picker.value = personId;

    try {
      const res = await fetch(`${API_BASE}/people/${personId}/ledger`);
      const json = await res.json();
      if (json.status !== 'success') return;
      const d = json.data;

      document.getElementById('ledger-hero-card').style.display = 'block';
      document.getElementById('ledger-name').textContent = d.person.full_name;
      document.getElementById('ledger-contact').textContent = `Mobile: ${d.person.mobile_number || 'N/A'} | Email: ${d.person.email || 'N/A'}`;

      document.getElementById('ledger-to-collect').textContent = formatCurrency(d.summary.remaining_to_collect);
      document.getElementById('ledger-given-collected').textContent = `Total Given: ${formatCurrency(d.summary.total_lent)} | Collected: ${formatCurrency(d.summary.total_collected)}`;

      document.getElementById('ledger-to-pay').textContent = formatCurrency(d.summary.remaining_to_pay);
      document.getElementById('ledger-borrowed-repaid').textContent = `Total Borrowed: ${formatCurrency(d.summary.total_borrowed)} | Repaid: ${formatCurrency(d.summary.total_repaid)}`;

      const net = d.summary.net_balance;
      const netBadge = document.getElementById('ledger-net-badge');
      const netAmt = document.getElementById('ledger-net-amt');
      const netLabel = document.getElementById('ledger-net-label');

      netAmt.textContent = formatCurrency(Math.abs(net));
      if (net > 0) {
        netBadge.className = 'badge badge-completed';
        netBadge.textContent = 'Net Receivable (They Owe You)';
        netLabel.textContent = `${d.person.full_name} owes you ${formatCurrency(net)}`;
      } else if (net < 0) {
        netBadge.className = 'badge badge-overdue';
        netBadge.textContent = 'Net Payable (You Owe Them)';
        netLabel.textContent = `You owe ${d.person.full_name} ${formatCurrency(Math.abs(net))}`;
      } else {
        netBadge.className = 'badge badge-partially';
        netBadge.textContent = 'Fully Settled';
        netLabel.textContent = 'All mutual debts & loans settled';
      }

      const tbody = document.getElementById('ledger-activities-body');
      if (d.activities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">No financial activity recorded with this person yet.</td></tr>';
        return;
      }

      tbody.innerHTML = d.activities.map(a => `
        <tr>
          <td><strong>${a.date}</strong></td>
          <td><span class="badge ${a.type.includes('Lent') ? 'badge-partially' : a.type.includes('Borrowed') ? 'badge-pending' : 'badge-completed'}">${a.type}</span></td>
          <td><code>${a.ref || '-'}</code></td>
          <td style="font-size:0.8rem; color:var(--text-muted);">${a.direction}</td>
          <td>${a.account_name || '-'}</td>
          <td style="font-weight:700;">${formatCurrency(a.amount)}</td>
          <td>${a.notes || '-'}</td>
        </tr>
      `).join('');
    } catch (e) {
      console.error(e);
    }
  }
};

// -------------------------------------------------------------
// MODULE 9: UNIFIED TRANSACTION REGISTER (FR-09)
// -------------------------------------------------------------
const TransactionModule = {
  async load() {
    const search = document.getElementById('txn-search')?.value || '';
    const type = document.getElementById('txn-type-filter')?.value || '';
    const account_id = document.getElementById('txn-account-filter')?.value || '';
    const start_date = document.getElementById('txn-start-date')?.value || '';
    const end_date = document.getElementById('txn-end-date')?.value || '';

    const params = new URLSearchParams({ search, type, account_id, start_date, end_date });
    try {
      const res = await fetch(`${API_BASE}/transactions?${params}`);
      const json = await res.json();
      const tbody = document.getElementById('transactions-table-body');
      if (!tbody) return;

      if (!json.data || json.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted);">No transactions match your search / filter criteria.</td></tr>';
        return;
      }

      tbody.innerHTML = json.data.map(t => {
        const isPositive = ['Income', 'Loan Collection'].includes(t.transaction_type);
        const isNegative = ['Expense', 'Loan Repayment'].includes(t.transaction_type);
        const amtClass = isPositive ? 'amt-positive' : isNegative ? 'amt-negative' : 'amt-neutral';
        const sign = isPositive ? '+' : isNegative ? '-' : '';

        return `
          <tr>
            <td><code>${t.transaction_ref}</code></td>
            <td>${t.transaction_date}</td>
            <td><span class="badge ${isPositive ? 'badge-completed' : isNegative ? 'badge-overdue' : 'badge-partially'}">${t.transaction_type}</span></td>
            <td><strong>${t.description}</strong><br><small style="color:var(--text-muted);">${t.notes || ''}</small></td>
            <td>${t.person_name || '-'}</td>
            <td>${t.account_name || '-'}</td>
            <td class="${amtClass}" style="font-weight:700;">${sign}${formatCurrency(t.amount)}</td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.error(e);
    }
  }
};

// -------------------------------------------------------------
// MODULE 10: ACCOUNTS MANAGEMENT (FR-10)
// -------------------------------------------------------------
const AccountModule = {
  async load() {
    try {
      const res = await fetch(`${API_BASE}/accounts`);
      const json = await res.json();
      if (json.status !== 'success') return;
      globalAccounts = json.data;

      const cardsGrid = document.getElementById('accounts-cards-grid');
      if (cardsGrid) {
        cardsGrid.innerHTML = globalAccounts.map(a => `
          <div class="kpi-card">
            <div class="kpi-header">
              <span class="kpi-title">${a.account_name}</span>
              <div class="kpi-icon balance"><i data-lucide="credit-card"></i></div>
            </div>
            <div class="kpi-value ${a.current_balance >= 0 ? 'amt-positive' : 'amt-negative'}">${formatCurrency(a.current_balance)}</div>
            <div class="kpi-subtext">${a.account_type} ${a.bank_name ? '• ' + a.bank_name : ''}</div>
          </div>
        `).join('');
      }

      const tbody = document.getElementById('accounts-table-body');
      if (tbody) {
        tbody.innerHTML = globalAccounts.map(a => `
          <tr>
            <td><strong>${a.account_name}</strong><br><small style="color:var(--text-muted);">${a.bank_name || ''} ${a.account_number || ''}</small></td>
            <td>${a.account_type}</td>
            <td>${formatCurrency(a.opening_balance)}</td>
            <td class="${a.current_balance >= 0 ? 'amt-positive' : 'amt-negative'}" style="font-weight:700;">${formatCurrency(a.current_balance)}</td>
            <td><span class="badge ${a.status === 'Active' ? 'badge-active' : 'badge-inactive'}">${a.status}</span></td>
            <td>
              <div style="display:flex; gap:6px;">
                <button class="btn-secondary btn-sm" onclick="AccountModule.edit('${a.ROWID}')"><i data-lucide="edit-2"></i></button>
              </div>
            </td>
          </tr>
        `).join('');
      }

      lucide.createIcons();
      populateAccountDropdowns();
    } catch (e) {
      console.error(e);
    }
  },

  async save(e) {
    e.preventDefault();
    const id = document.getElementById('account-id').value;
    const payload = {
      account_name: document.getElementById('form-account-name').value,
      account_type: document.getElementById('form-account-type').value,
      opening_balance: document.getElementById('form-account-opening').value,
      bank_name: document.getElementById('form-account-bank').value,
      account_number: document.getElementById('form-account-number').value,
      notes: document.getElementById('form-account-notes').value
    };

    const url = id ? `${API_BASE}/accounts/${id}` : `${API_BASE}/accounts`;
    const method = id ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast(id ? 'Account updated' : 'Account created', 'success');
        closeModal('modal-account');
        document.getElementById('form-account').reset();
        document.getElementById('account-id').value = '';
        AccountModule.load();
        DashboardModule.load();
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error saving account: ' + err.message, 'error');
    }
  },

  async edit(id) {
    try {
      const res = await fetch(`${API_BASE}/accounts/${id}`);
      const json = await res.json();
      if (json.status === 'success') {
        const d = json.data;
        document.getElementById('account-id').value = d.ROWID;
        document.getElementById('form-account-name').value = d.account_name;
        document.getElementById('form-account-type').value = d.account_type;
        document.getElementById('form-account-opening').value = d.opening_balance;
        document.getElementById('form-account-bank').value = d.bank_name || '';
        document.getElementById('form-account-number').value = d.account_number || '';
        document.getElementById('form-account-notes').value = d.notes || '';
        document.getElementById('modal-account-title').textContent = 'Edit Account';
        openModal('modal-account');
      }
    } catch (e) {
      showToast('Error fetching account: ' + e.message, 'error');
    }
  },

  async transfer(e) {
    e.preventDefault();
    const payload = {
      from_account_id: document.getElementById('form-transfer-from').value,
      to_account_id: document.getElementById('form-transfer-to').value,
      amount: document.getElementById('form-transfer-amount').value,
      transfer_date: document.getElementById('form-transfer-date').value,
      notes: document.getElementById('form-transfer-notes').value
    };

    try {
      const res = await fetch(`${API_BASE}/accounts/transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Internal transfer executed successfully!', 'success');
        closeModal('modal-transfer');
        document.getElementById('form-transfer').reset();
        AccountModule.load();
        DashboardModule.load();
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error executing transfer: ' + err.message, 'error');
    }
  }
};

// -------------------------------------------------------------
// MODULE 11: REMINDERS (FR-11)
// -------------------------------------------------------------
const RemindersModule = {
  async load() {
    try {
      const res = await fetch(`${API_BASE}/reminders`);
      const json = await res.json();
      if (json.status !== 'success') return;
      const d = json.data;

      // Overdue
      const overdueBody = document.getElementById('overdue-reminders-body');
      const overdueList = [
        ...(d.overdue_repayments || []).map(r => ({ ...r, type: 'Repayment Overdue', isPayable: true })),
        ...(d.overdue_collections || []).map(c => ({ ...c, type: 'Collection Overdue', isPayable: false }))
      ];

      if (overdueList.length === 0) {
        overdueBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:24px; color:var(--text-muted);">No overdue obligations. All payments up to date!</td></tr>';
      } else {
        overdueBody.innerHTML = overdueList.map(item => `
          <tr>
            <td><span class="badge badge-overdue">${item.type}</span></td>
            <td><strong>${item.person_name}</strong></td>
            <td class="${item.isPayable ? 'amt-negative' : 'amt-positive'}">${formatCurrency(item.isPayable ? item.outstanding_payable : item.outstanding_receivable)}</td>
            <td><strong style="color:var(--danger);">${item.due_date || item.expected_return_date}</strong></td>
            <td>
              ${item.isPayable 
                ? `<button class="btn-primary btn-sm" onclick="BorrowModule.openRepayModal('${item.ROWID}', '${item.person_name}', ${item.outstanding_payable})">Repay Now</button>`
                : `<div style="display:flex; gap:6px;"><button class="btn-primary btn-sm" style="background-color:var(--info);" onclick="LendModule.openCollectModal('${item.ROWID}', '${item.person_name}', ${item.outstanding_receivable})">Collect Now</button><button class="btn-secondary btn-sm" style="color:var(--primary);" onclick="NotificationModule.sendDueReminder('${item.ROWID}', '${item.type}')" title="Send SMS Due Reminder to Phone"><i data-lucide="message-square"></i></button></div>`}
            </td>
          </tr>
        `).join('');
      }

      // Upcoming
      const upcomingBody = document.getElementById('upcoming-reminders-body');
      const upcomingList = [
        ...(d.upcoming_repayments || []).map(r => ({ ...r, type: 'Upcoming Repayment', isPayable: true })),
        ...(d.upcoming_collections || []).map(c => ({ ...c, type: 'Upcoming Collection', isPayable: false }))
      ];

      if (upcomingList.length === 0) {
        upcomingBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:24px; color:var(--text-muted);">No obligations due in the next 7 days.</td></tr>';
      } else {
        upcomingBody.innerHTML = upcomingList.map(item => `
          <tr>
            <td><span class="badge badge-pending">${item.type}</span></td>
            <td><strong>${item.person_name}</strong></td>
            <td class="${item.isPayable ? 'amt-negative' : 'amt-positive'}">${formatCurrency(item.isPayable ? item.outstanding_payable : item.outstanding_receivable)}</td>
            <td>${item.due_date || item.expected_return_date}</td>
            <td>
              ${item.isPayable 
                ? `<button class="btn-primary btn-sm" onclick="BorrowModule.openRepayModal('${item.ROWID}', '${item.person_name}', ${item.outstanding_payable})">Repay</button>`
                : `<div style="display:flex; gap:6px;"><button class="btn-primary btn-sm" style="background-color:var(--info);" onclick="LendModule.openCollectModal('${item.ROWID}', '${item.person_name}', ${item.outstanding_receivable})">Collect</button><button class="btn-secondary btn-sm" style="color:var(--primary);" onclick="NotificationModule.sendDueReminder('${item.ROWID}', '${item.type}')" title="Send SMS Reminder to Phone"><i data-lucide="message-square"></i></button></div>`}
            </td>
          </tr>
        `).join('');
      }

      RemindersModule.checkCount();
    } catch (e) {
      console.error(e);
    }
  },

  async checkCount() {
    try {
      const res = await fetch(`${API_BASE}/reminders`);
      const json = await res.json();
      if (json.status === 'success') {
        const d = json.data;
        const count = (d.overdue_repayments?.length || 0) + (d.overdue_collections?.length || 0) +
                      (d.upcoming_repayments?.length || 0) + (d.upcoming_collections?.length || 0);
        const badge = document.getElementById('topbar-notif-count');
        if (badge) {
          badge.textContent = count;
          badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
      }
    } catch (e) {}
  }
};

// -------------------------------------------------------------
// MODULE 12: FINANCIAL REPORTS (FR-12)
// -------------------------------------------------------------
const ReportModule = {
  async load() {
    const reportType = document.getElementById('report-type-picker')?.value || 'monthly_income';
    const startDate = document.getElementById('report-start-date')?.value || '';
    const endDate = document.getElementById('report-end-date')?.value || '';

    const heading = document.getElementById('report-type-picker').selectedOptions[0].text;
    document.getElementById('report-title-heading').textContent = heading;

    try {
      const res = await fetch(`${API_BASE}/reports/${reportType}?start_date=${startDate}&end_date=${endDate}`);
      const json = await res.json();
      if (json.status !== 'success') return;
      const data = json.data;

      const thead = document.getElementById('report-table-head');
      const tbody = document.getElementById('report-table-body');

      if (!data || data.length === 0) {
        thead.innerHTML = '';
        tbody.innerHTML = '<tr><td style="text-align:center; padding:24px; color:var(--text-muted);">No records found for the selected report and date range.</td></tr>';
        return;
      }

      const keys = Object.keys(data[0]);
      thead.innerHTML = `<tr>${keys.map(k => `<th>${k.replace(/_/g, ' ').toUpperCase()}</th>`).join('')}</tr>`;
      
      tbody.innerHTML = data.map(row => `
        <tr>
          ${keys.map(k => {
            let val = row[k];
            if (typeof val === 'number') {
              if (k.includes('amount') || k.includes('total') || k.includes('balance') || k.includes('average')) {
                val = formatCurrency(val);
              }
            }
            return `<td>${val !== null && val !== undefined ? val : '-'}</td>`;
          }).join('')}
        </tr>
      `).join('');

    } catch (e) {
      console.error(e);
    }
  }
};

// -------------------------------------------------------------
// MODULE 13: SETTINGS & CATEGORIES (FR-13)
// -------------------------------------------------------------
const SettingsModule = {
  async load() {
    try {
      const [setRes, catRes] = await Promise.all([
        fetch(`${API_BASE}/settings`).then(r => r.json()).catch(() => ({ status: 'error' })),
        fetch(`${API_BASE}/categories`).then(r => r.json()).catch(() => ({ status: 'error' }))
      ]);

      if (setRes.status === 'success') {
        const s = setRes.data;
        if (s.currency_symbol) document.getElementById('setting-currency-symbol').value = s.currency_symbol;
        if (s.currency_code) document.getElementById('setting-currency-code').value = s.currency_code;
        if (s.theme) document.getElementById('setting-theme').value = s.theme;
        if (s.default_country_code) document.getElementById('setting-country-code').value = s.default_country_code;
        if (s.notif_channel) document.getElementById('setting-notif-channel').value = s.notif_channel;
        if (s.sms_api_key) document.getElementById('setting-sms-api-key').value = s.sms_api_key;
        if (s.sms_sender_id) document.getElementById('setting-sms-sender-id').value = s.sms_sender_id;
      }

      if (catRes.status === 'success') {
        const tbody = document.getElementById('settings-categories-body');
        if (tbody) {
          tbody.innerHTML = catRes.data.map(c => `
            <tr>
              <td><strong>${c.category_name}</strong></td>
              <td><span class="badge ${c.category_type === 'Expense' ? 'badge-overdue' : 'badge-completed'}">${c.category_type}</span></td>
              <td>
                ${!c.is_default ? `<button class="btn-secondary btn-sm" style="color:var(--danger);" onclick="CategoryModule.delete('${c.ROWID}')"><i data-lucide="trash-2"></i></button>` : '<small style="color:var(--text-muted);">System Default</small>'}
              </td>
            </tr>
          `).join('');
          lucide.createIcons();
        }
      }
    } catch (e) {
      console.error(e);
    }
  },

  async saveSettings() {
    const payload = {
      currency_symbol: document.getElementById('setting-currency-symbol').value,
      currency_code: document.getElementById('setting-currency-code').value,
      theme: document.getElementById('setting-theme').value
    };

    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Settings saved successfully', 'success');
        appSettings.currency_symbol = payload.currency_symbol;
        appSettings.currency_code = payload.currency_code;
        if (currentTheme !== payload.theme) {
          applyTheme(payload.theme);
        } else {
          DashboardModule.load();
        }
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (e) {
      showToast('Error saving settings: ' + e.message, 'error');
    }
  },

  async saveNotificationSettings() {
    const payload = {
      default_country_code: document.getElementById('setting-country-code').value,
      notif_channel: document.getElementById('setting-notif-channel').value,
      sms_api_key: document.getElementById('setting-sms-api-key').value,
      sms_sender_id: document.getElementById('setting-sms-sender-id').value
    };

    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('SMS configuration saved successfully!', 'success');
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (e) {
      showToast('Error saving notification preferences: ' + e.message, 'error');
    }
  }
};

const CategoryModule = {
  async save(e) {
    e.preventDefault();
    const payload = {
      category_name: document.getElementById('form-cat-name').value,
      category_type: document.getElementById('form-cat-type').value,
      color: document.getElementById('form-cat-color').value,
      icon: document.getElementById('form-cat-icon').value
    };

    try {
      const res = await fetch(`${API_BASE}/categories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Category created successfully', 'success');
        closeModal('modal-category');
        document.getElementById('form-category').reset();
        await loadInitialData();
        SettingsModule.load();
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (err) {
      showToast('Error creating category: ' + err.message, 'error');
    }
  },

  async delete(id) {
    if (!confirm('Are you sure you want to delete this custom category?')) return;
    try {
      const res = await fetch(`${API_BASE}/categories/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.status === 'success') {
        showToast('Category deleted', 'success');
        await loadInitialData();
        SettingsModule.load();
      } else {
        showToast(getErrorMessage(json), 'error');
      }
    } catch (e) {
      showToast('Error deleting category', 'error');
    }
  }
};

// CSV Export Utility
function exportTableToCSV(tableId, filename) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const rows = [];
  table.querySelectorAll('tr').forEach(tr => {
    const row = [];
    tr.querySelectorAll('th, td').forEach(cell => {
      let text = cell.innerText.replace(/"/g, '""').trim();
      row.push(`"${text}"`);
    });
    if (row.length > 0) rows.push(row.join(','));
  });

  const csvContent = 'data:text/csv;charset=utf-8,' + rows.join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
}
