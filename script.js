document.addEventListener('DOMContentLoaded', () => {

    // =====================================================
    //  CURRENCY CONFIGURATION
    // =====================================================
    const CURRENCIES = {
        INR: { name: "Indian Rupee",        symbol: "₹" },
        USD: { name: "US Dollar",           symbol: "$" },
        EUR: { name: "Euro",                symbol: "€" },
        GBP: { name: "British Pound",       symbol: "£" },
        JPY: { name: "Japanese Yen",        symbol: "¥" },
        CNY: { name: "Chinese Yuan",        symbol: "¥" },
        AUD: { name: "Australian Dollar",   symbol: "A$" },
        CAD: { name: "Canadian Dollar",     symbol: "C$" },
        SGD: { name: "Singapore Dollar",    symbol: "S$" },
        AED: { name: "UAE Dirham",          symbol: "د.إ" },
        SAR: { name: "Saudi Riyal",         symbol: "﷼" },
        QAR: { name: "Qatari Riyal",        symbol: "ر.ق" },
        KWD: { name: "Kuwaiti Dinar",       symbol: "د.ك" },
        CHF: { name: "Swiss Franc",         symbol: "CHF" },
        NZD: { name: "New Zealand Dollar",  symbol: "NZ$" },
        ZAR: { name: "South African Rand",  symbol: "R" },
        BRL: { name: "Brazilian Real",      symbol: "R$" },
        MXN: { name: "Mexican Peso",        symbol: "Mex$" },
        KRW: { name: "South Korean Won",    symbol: "₩" },
        THB: { name: "Thai Baht",           symbol: "฿" },
        MYR: { name: "Malaysian Ringgit",   symbol: "RM" },
        IDR: { name: "Indonesian Rupiah",   symbol: "Rp" },
        PHP: { name: "Philippine Peso",     symbol: "₱" },
        HKD: { name: "Hong Kong Dollar",    symbol: "HK$" },
        TRY: { name: "Turkish Lira",        symbol: "₺" },
        SEK: { name: "Swedish Krona",       symbol: "kr" },
        NOK: { name: "Norwegian Krone",     symbol: "kr" },
        DKK: { name: "Danish Krone",        symbol: "kr" },
        PLN: { name: "Polish Zloty",        symbol: "zł" },
        RUB: { name: "Russian Ruble",       symbol: "₽" }
    };

    // =====================================================
    //  STATE & STORAGE KEYS
    // =====================================================
    const SETTINGS_KEY = 'expenseiq_settings';
    const EXPENSES_KEY = 'expenseiq_expenses';
    const RATES_KEY    = 'expenseiq_rates_cache';
    const BUDGET_KEY   = 'expenseiq_budget';

    let expenses         = [];
    let settings         = { currency: 'INR' };
    let chartInstance    = null;
    let currentChartType = 'bar';
    let budget           = 0;       // Monthly budget (0 = not set)
    let timePeriod       = 'monthly'; // Default time period

    // Exchange rates
    let exchangeRates    = {};
    let ratesBaseCurrency = 'USD';
    let ratesTimestamp   = null;

    // =====================================================
    //  DOM ELEMENTS  (all inside DOMContentLoaded)
    // =====================================================
    const form                  = document.getElementById('expense-form');
    const expensesTableBody     = document.querySelector('#expenses-table tbody');
    const dashboardTotal        = document.getElementById('total-spent-amount');
    const dashboardThisMonth    = document.getElementById('this-month-amount');
    const dashboardCount        = document.getElementById('expense-count');
    const dashboardHighest      = document.getElementById('highest-expense-amount');
    const currencySelect        = document.getElementById('currency');
    const searchInput           = document.getElementById('search-search');
    const categoryFilter        = document.getElementById('filter-category');
    const monthFilter           = document.getElementById('filter-month');
    const chartCanvas           = document.getElementById('spendingChart');
    const noChartMsg            = document.getElementById('no-chart-msg');
    const exportCsvBtn          = document.getElementById('export-csv-btn');
    const exportReportBtn       = document.getElementById('export-report-btn');
    const csvFileInput          = document.getElementById('csv-file-input');
    const chartTypeTabs         = document.getElementById('chart-type-tabs');
    const toastContainer        = document.getElementById('toast-container');
    const liveBadge             = document.getElementById('live-badge');
    const rateStatusEl          = document.getElementById('rate-status');
    const rateStatusText        = document.getElementById('rate-status-text');
    const exchangeInfoEl        = document.getElementById('exchange-info');
    const exchangeRateDisplay   = document.getElementById('exchange-rate-display');
    const exchangeRateTimestampEl = document.getElementById('exchange-rate-timestamp');
    const amountCurrencyLabel   = document.getElementById('amount-currency-label');
    const currencySymbolPrefix  = document.getElementById('currency-symbol-prefix');
    const expenseBadge          = document.getElementById('expense-badge');

    // Budget elements
    const budgetAmountInput     = document.getElementById('budget-amount');
    const budgetCurrencySpan    = document.getElementById('budget-currency');
    const budgetDisplayAmount   = document.getElementById('budget-display-amount');
    const budgetSpentAmount     = document.getElementById('budget-spent-amount');
    const budgetRemainingAmount = document.getElementById('budget-remaining-amount');
    const budgetProgressFill    = document.getElementById('budget-progress-fill');
    const budgetWarning         = document.getElementById('budget-warning');

    // Time period elements
    const periodTabs            = document.querySelectorAll('.period-tab');
    const periodTotalAmount     = document.getElementById('period-total-amount');

    // Extended dashboard elements
    const dashboardBudgetAmount    = document.getElementById('dashboard-budget-amount');
    const dashboardRemainingAmount = document.getElementById('dashboard-remaining-amount');
    const dashboardTopCategory     = document.getElementById('dashboard-top-category');

    // Edit expense modal elements
    const editExpenseModal        = document.getElementById('edit-expense-modal');
    const editModalCloseBtn       = document.getElementById('edit-modal-close');
    const editExpenseForm         = document.getElementById('edit-expense-form');
    const editExpenseIdInput      = document.getElementById('edit-expense-id');
    const editAmountInput         = document.getElementById('edit-amount');
    const editCategorySelect      = document.getElementById('edit-category');
    const editDateInput           = document.getElementById('edit-date');
    const editNoteInput           = document.getElementById('edit-note');
    const editCancelBtn           = document.getElementById('edit-cancel-btn');
    const editAmountCurrencyLabel = document.getElementById('edit-amount-currency-label');
    const editCurrencySymbolPrefix = document.getElementById('edit-currency-symbol-prefix');

    // Delete confirmation modal elements
    const deleteConfirmModal   = document.getElementById('delete-confirm-modal');
    const deleteModalCloseBtn  = document.getElementById('delete-modal-close');
    const deleteConfirmBtn     = document.getElementById('delete-confirm-btn');
    const deleteCancelBtn      = document.getElementById('delete-cancel-btn');
    const deleteExpensePreview = document.getElementById('delete-expense-preview');

    // Backup / Restore elements
    const backupJsonBtn        = document.getElementById('backup-json-btn');
    const restoreJsonInput     = document.getElementById('restore-json-input');

    // Pending delete ID (set when the confirmation modal is opened)
    let pendingDeleteId = null;

    // =====================================================
    //  TOAST NOTIFICATIONS
    // =====================================================
    function showToast(message, type = 'info', duration = 4000) {
        const icons = {
            success: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
            error: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
            warning: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
            info: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
        };
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span>${message}</span>
            <button class="toast-close" onclick="this.closest('.toast').remove()" aria-label="Close">&times;</button>
        `;
        toastContainer.appendChild(toast);
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('removing');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    }

    // =====================================================
    //  SETTINGS
    // =====================================================
    function loadSettings() {
        try {
            const saved = localStorage.getItem(SETTINGS_KEY);
            if (saved) {
                settings = JSON.parse(saved);
                if (!CURRENCIES[settings.currency]) settings.currency = 'INR';
            }
        } catch (e) {
            settings = { currency: 'INR' };
        }
    }

    function saveSettings() {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    }

    // =====================================================
    //  BUDGET PERSISTENCE
    // =====================================================
    function loadBudget() {
        try {
            const saved = localStorage.getItem(BUDGET_KEY);
            if (saved !== null) {
                budget = parseFloat(saved) || 0;
                if (budget > 0) budgetAmountInput.value = budget;
            }
        } catch (e) {
            budget = 0;
        }
    }

    function saveBudget() {
        localStorage.setItem(BUDGET_KEY, String(budget));
    }

    // =====================================================
    //  EXPENSES — CSV BACKEND (via HTTP API)
    //  Primary source of truth: data/expenses.csv
    //  localStorage is only used for one-time migration.
    // =====================================================
    const API_BASE = '/api/expenses';

    async function parseApiResponse(res) {
        const contentType = res.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
            const raw = await res.text();
            const cleanText = raw.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 80);
            throw new Error(`Server returned non-JSON response (${res.status}): ${cleanText || 'HTML/Text response'}`);
        }
        return await res.json();
    }

    async function loadExpenses() {
        try {
            const res = await fetch(API_BASE);
            const data = await parseApiResponse(res);
            if (!res.ok || !data.success) throw new Error(data.error || 'HTTP ' + res.status);

            if (data.expenses.length === 0) {
                // First run: check localStorage for existing data to migrate
                await migrateFromLocalStorage();
            } else {
                expenses = data.expenses;
            }
        } catch (e) {
            console.error('Failed to load expenses from backend:', e);
            showToast('Could not load expenses from server. Is the backend running?', 'error', 8000);
            expenses = [];
        }
    }

    /** One-time migration: push localStorage expenses to the CSV backend. */
    async function migrateFromLocalStorage() {
        try {
            const saved = localStorage.getItem(EXPENSES_KEY);
            if (!saved) return;
            const local = JSON.parse(saved);
            if (!Array.isArray(local) || local.length === 0) return;

            // Ensure every record has required fields before sending
            const toMigrate = local
                .filter(exp => exp && exp.date && exp.category && exp.amount > 0)
                .map(exp => ({
                    id:       exp.id || (Date.now().toString() + Math.random().toString(36).slice(2)),
                    date:     exp.date,
                    amount:   parseFloat(exp.amount),
                    currency: exp.currency || settings.currency,
                    category: exp.category,
                    note:     exp.note || ''
                }));

            if (toMigrate.length === 0) return;

            const res = await fetch(API_BASE + '/bulk', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ expenses: toMigrate, mode: 'replace' })
            });
            const data = await parseApiResponse(res);
            if (data.success) {
                expenses = toMigrate;
                // Clear localStorage expenses to avoid future duplication
                localStorage.removeItem(EXPENSES_KEY);
                showToast(`Migrated ${toMigrate.length} expense(s) from browser storage to CSV.`, 'success', 6000);
                console.log('[Migration] Moved', toMigrate.length, 'expenses to expenses.csv');
            } else {
                throw new Error(data.error || 'Bulk API error');
            }
        } catch (e) {
            console.error('[Migration] Failed:', e);
            expenses = [];
        }
    }

    // saveExpenses() is kept as a no-op so no existing call-site breaks.
    // All persistence now happens through the individual API calls below.
    function saveExpenses() {
        // No-op: expenses are persisted to CSV by the backend on each CRUD call.
    }

    // =====================================================
    //  REAL-TIME EXCHANGE RATES (open.er-api.com)
    // =====================================================
    function setRateStatus(fetching) {
        if (fetching) {
            rateStatusEl.classList.remove('hidden');
            rateStatusText.textContent = 'Fetching live rates…';
        } else {
            setTimeout(() => rateStatusEl.classList.add('hidden'), 2000);
        }
    }

    async function fetchExchangeRates() {
        // Always base on INR so we can derive any currency rate relative to INR
        const baseCurrency = 'INR';
        const cached = getCachedRates(baseCurrency);
        if (cached) {
            exchangeRates = cached.rates;
            ratesBaseCurrency = baseCurrency;
            ratesTimestamp = cached.timestamp;
            updateLiveBadge(true);
            updateExchangeInfoDisplay();
            return true;
        }

        // Show loading state in exchange info panel
        exchangeRateDisplay.textContent = 'Loading rate…';
        exchangeInfoEl.classList.remove('hidden');
        setRateStatus(true);
        try {
            const res = await fetch(`https://open.er-api.com/v6/latest/${baseCurrency}`);
            if (!res.ok) throw new Error('Network error');
            const data = await res.json();
            if (data.result !== 'success') throw new Error('API error');

            exchangeRates = data.rates;
            ratesBaseCurrency = baseCurrency;
            ratesTimestamp = Date.now();
            setCachedRates(baseCurrency, exchangeRates, ratesTimestamp);
            updateLiveBadge(true);
            updateExchangeInfoDisplay();
            setRateStatus(false);
            return true;
        } catch (err) {
            console.warn('Exchange rate fetch failed:', err);
            updateLiveBadge(false);
            exchangeRateDisplay.textContent = 'Rate unavailable';
            exchangeInfoEl.classList.remove('hidden');
            setRateStatus(false);
            showToast('Could not fetch live rates. Amounts shown in original currency.', 'warning', 6000);
            return false;
        }
    }

    function getCachedRates(base) {
        try {
            const raw = localStorage.getItem(RATES_KEY);
            if (!raw) return null;
            const cache = JSON.parse(raw);
            if (cache.base !== base) return null;
            if (Date.now() - cache.timestamp > 60 * 60 * 1000) return null; // 1 hour TTL
            return cache;
        } catch { return null; }
    }

    function setCachedRates(base, rates, timestamp) {
        try {
            localStorage.setItem(RATES_KEY, JSON.stringify({ base, rates, timestamp }));
        } catch (e) { /* ignore */ }
    }

    function updateLiveBadge(isLive) {
        if (isLive) {
            liveBadge.classList.remove('offline');
            liveBadge.querySelector('.live-dot').style.background = 'var(--accent-success)';
        } else {
            liveBadge.classList.add('offline');
        }
    }

    // =====================================================
    //  LIVE EXCHANGE RATE DISPLAY (Base: INR)
    // =====================================================
    function updateExchangeInfoDisplay() {
        const cur = settings.currency;

        // If INR is selected, show static 1:1
        if (cur === 'INR') {
            exchangeRateDisplay.textContent = '1 INR = ₹1.00';
            exchangeRateTimestampEl.textContent = '';
            exchangeInfoEl.classList.remove('hidden');
            return;
        }

        // If rates haven't loaded yet, show loading
        if (!exchangeRates || Object.keys(exchangeRates).length === 0) {
            exchangeRateDisplay.textContent = 'Loading rate…';
            exchangeRateTimestampEl.textContent = '';
            exchangeInfoEl.classList.remove('hidden');
            return;
        }

        // ratesBaseCurrency is always INR now.
        // exchangeRates[cur] = how many of `cur` per 1 INR
        // We want: 1 cur = ? INR  → 1 / exchangeRates[cur]
        const ratePerInr = exchangeRates[cur];
        if (!ratePerInr || ratePerInr === 0) {
            exchangeRateDisplay.textContent = 'Rate unavailable';
            exchangeRateTimestampEl.textContent = '';
            exchangeInfoEl.classList.remove('hidden');
            return;
        }

        const inrPerOne = 1 / ratePerInr;
        const sym = CURRENCIES[cur]?.symbol || cur;
        const formattedRate = inrPerOne >= 1
            ? inrPerOne.toFixed(2)
            : inrPerOne.toPrecision(4);

        exchangeRateDisplay.textContent = `1 ${sym} = ₹${formattedRate}`;

        if (ratesTimestamp) {
            const updatedAt = new Date(ratesTimestamp).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
            exchangeRateTimestampEl.textContent = `Updated: ${updatedAt}`;
        } else {
            exchangeRateTimestampEl.textContent = '';
        }
        exchangeInfoEl.classList.remove('hidden');
    }

    /**
     * Convert amount from `fromCurrency` to `toCurrency`.
     * Returns null if rates unavailable.
     */
    function convertAmount(amount, fromCurrency, toCurrency) {
        if (fromCurrency === toCurrency) return amount;
        if (!exchangeRates || Object.keys(exchangeRates).length === 0) return null;

        let amountInBase;
        if (fromCurrency === ratesBaseCurrency) {
            amountInBase = amount;
        } else {
            const rateFrom = exchangeRates[fromCurrency];
            if (!rateFrom) return null;
            amountInBase = amount / rateFrom;
        }
        if (toCurrency === ratesBaseCurrency) return amountInBase;
        const rateTo = exchangeRates[toCurrency];
        if (!rateTo) return null;
        return amountInBase * rateTo;
    }

    // =====================================================
    //  FORMAT HELPERS
    // =====================================================
    function formatCurrency(amount, currency) {
        if (typeof amount !== 'number' || isNaN(amount)) amount = 0;
        try {
            return new Intl.NumberFormat(undefined, {
                style: 'currency',
                currency,
                maximumFractionDigits: currency === 'JPY' || currency === 'KRW' ? 0 : 2
            }).format(amount);
        } catch (e) {
            const sym = CURRENCIES[currency]?.symbol || currency;
            return `${sym}${amount.toFixed(2)}`;
        }
    }

    function formatNumber(n, decimals = 2) {
        return parseFloat(n.toFixed(decimals)).toLocaleString();
    }

    function getMonthFromDate(dateStr) {
        return dateStr.slice(0, 7);
    }

    function getCurrentMonth() {
        return new Date().toISOString().slice(0, 7);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatDisplayDate(dateStr) {
        try {
            const d = new Date(dateStr + 'T00:00:00');
            return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
        } catch { return dateStr; }
    }

    // =====================================================
    //  CURRENCY SELECTOR (no blank option)
    // =====================================================
    function populateCurrencySelector() {
        currencySelect.innerHTML = '';
        Object.entries(CURRENCIES).forEach(([code, info]) => {
            const option = document.createElement('option');
            option.value = code;
            option.textContent = `${code} (${info.symbol}) - ${info.name}`;
            currencySelect.appendChild(option);
        });
        currencySelect.value = settings.currency;
    }

    function updateCurrencyUI() {
        const cur = CURRENCIES[settings.currency];
        if (cur) {
            amountCurrencyLabel.textContent      = `(${settings.currency})`;
            currencySymbolPrefix.textContent     = cur.symbol;
            editAmountCurrencyLabel.textContent  = `(${settings.currency})`;
            editCurrencySymbolPrefix.textContent = cur.symbol;
            budgetCurrencySpan.textContent       = cur.symbol;
        }
        updateExchangeInfoDisplay();
    }

    // =====================================================
    //  TIME PERIOD HELPERS
    // =====================================================
    function getPeriodStartEnd(period) {
        const now = new Date();
        let start, end;
        switch (period) {
            case 'daily':
                start = end = now;
                break;
            case 'weekly':
                start = new Date(now);
                start.setDate(now.getDate() - now.getDay());
                end = new Date(now);
                end.setDate(now.getDate() + (6 - now.getDay()));
                break;
            case 'monthly':
                start = new Date(now.getFullYear(), now.getMonth(), 1);
                end   = new Date(now.getFullYear(), now.getMonth() + 1, 0);
                break;
            case 'yearly':
                start = new Date(now.getFullYear(), 0, 1);
                end   = new Date(now.getFullYear(), 11, 31);
                break;
            default:
                start = new Date(0); end = now;
        }
        return {
            start: start.toISOString().slice(0, 10),
            end:   end.toISOString().slice(0, 10)
        };
    }

    function filterExpensesByPeriod(exps, period) {
        const { start, end } = getPeriodStartEnd(period);
        const s = new Date(start), e = new Date(end);
        return exps.filter(exp => {
            const d = new Date(exp.date);
            return d >= s && d <= e;
        });
    }

    function getWeekNumber(dateStr) {
        const date = new Date(dateStr);
        const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
        const pastDays = (date - firstDayOfYear) / 86400000;
        return Math.ceil((pastDays + firstDayOfYear.getDay() + 1) / 7);
    }

    // =====================================================
    //  FILTERS
    // =====================================================
    function getFilteredExpenses() {
        const searchTerm = searchInput.value.trim().toLowerCase();
        const category   = categoryFilter.value;
        const month      = monthFilter.value;

        return expenses.filter(exp => {
            const matchesSearch   = searchTerm === '' ||
                (exp.note || '').toLowerCase().includes(searchTerm) ||
                exp.category.toLowerCase().includes(searchTerm);
            const matchesCategory = category === '' || exp.category === category;
            const matchesMonth    = month    === '' || getMonthFromDate(exp.date) === month;
            return matchesSearch && matchesCategory && matchesMonth;
        });
    }

    function populateCategories() {
        const saved = categoryFilter.value;          // remember current selection
        const categories = [...new Set(expenses.map(e => e.category))].sort();
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            categoryFilter.appendChild(opt);
        });
        categoryFilter.value = saved;                // restore selection
    }

    function populateMonthFilter() {
        const saved = monthFilter.value;             // remember current selection
        const months = [...new Set(expenses.map(e => getMonthFromDate(e.date)))].sort().reverse();
        monthFilter.innerHTML = '<option value="">All Months</option>';
        months.forEach(month => {
            const date  = new Date(month + '-01');
            const label = date.toLocaleString(undefined, { year: 'numeric', month: 'long' });
            const opt   = document.createElement('option');
            opt.value   = month;
            opt.textContent = label;
            monthFilter.appendChild(opt);
        });
        monthFilter.value = saved;                   // restore selection
    }

    // =====================================================
    //  ADVANCED CALCULATIONS
    // =====================================================
    function calculateAdvancedExpenses(exps) {
        if (exps.length === 0) {
            return { total: 0, monthly: 0, weekly: 0, average: 0, highest: 0, lowest: 0, count: 0, highestCategory: '', categoryTotals: {} };
        }
        const toCurrency   = settings.currency;
        const currentMonth = getCurrentMonth();
        const currentWeek  = getWeekNumber(new Date().toISOString().slice(0, 10));
        let total = 0, monthly = 0, weekly = 0, highest = 0, lowest = Infinity;
        const categoryTotals = {};

        exps.forEach(exp => {
            const converted = convertAmount(exp.amount, exp.currency, toCurrency);
            const val = converted !== null ? converted : exp.amount;
            total += val;
            if (getMonthFromDate(exp.date) === currentMonth) monthly += val;
            if (getWeekNumber(exp.date) === currentWeek)     weekly  += val;
            if (val > highest) highest = val;
            if (val < lowest)  lowest  = val;
            categoryTotals[exp.category] = (categoryTotals[exp.category] || 0) + val;
        });

        let highestCategory = '', highestCategoryAmount = 0;
        Object.entries(categoryTotals).forEach(([cat, amt]) => {
            if (amt > highestCategoryAmount) { highestCategoryAmount = amt; highestCategory = cat; }
        });

        return {
            total, monthly, weekly,
            average: total / exps.length,
            highest: highest === Infinity ? 0 : highest,
            lowest:  lowest  === Infinity ? 0 : lowest,
            count: exps.length, highestCategory, categoryTotals
        };
    }

    // =====================================================
    //  DASHBOARD
    // =====================================================
    function renderDashboard() {
        const filtered   = getFilteredExpenses();
        const toCurrency = settings.currency;
        // Determine what label "This Month" should mean:
        // - if the month filter is set, use that month; otherwise use the current calendar month
        const selectedMonth = monthFilter.value || getCurrentMonth();
        let totalConverted = 0, thisMonthConverted = 0, highestConverted = 0;

        filtered.forEach(exp => {
            const converted = convertAmount(exp.amount, exp.currency, toCurrency);
            const val = converted !== null ? converted : exp.amount;
            totalConverted += val;
            if (getMonthFromDate(exp.date) === selectedMonth) thisMonthConverted += val;
            if (val > highestConverted) highestConverted = val;
        });

        dashboardTotal.textContent     = formatCurrency(totalConverted, toCurrency);
        dashboardThisMonth.textContent = formatCurrency(thisMonthConverted, toCurrency);
        dashboardCount.textContent     = filtered.length;
        dashboardHighest.textContent   = formatCurrency(highestConverted, toCurrency);
        expenseBadge.textContent       = filtered.length;
    }

    function updateExtendedDashboard() {
        // Always use the currently filtered dataset so Top Category,
        // Budget and Remaining reflect the active category + month filters.
        const filtered = getFilteredExpenses();
        const advanced = calculateAdvancedExpenses(filtered);

        // Budget / Remaining cards
        if (budget > 0) {
            dashboardBudgetAmount.textContent = formatCurrency(budget, settings.currency);
            // Remaining = budget minus the filtered spending in the selected/current month
            const selectedMonth = monthFilter.value || getCurrentMonth();
            const monthFiltered = filtered.filter(exp => getMonthFromDate(exp.date) === selectedMonth);
            const monthlySpent  = monthFiltered.reduce((s, exp) => {
                const v = convertAmount(exp.amount, exp.currency, settings.currency);
                return s + (v !== null ? v : exp.amount);
            }, 0);
            dashboardRemainingAmount.textContent = formatCurrency(budget - monthlySpent, settings.currency);
        } else {
            dashboardBudgetAmount.textContent    = '-';
            dashboardRemainingAmount.textContent = '-';
        }

        // Top category - from filtered data only
        dashboardTopCategory.textContent = advanced.highestCategory || '-';
    }

    function updateBudgetUI() {
        const cur = CURRENCIES[settings.currency];
        if (cur) budgetCurrencySpan.textContent = cur.symbol;

        if (budget > 0) {
            budgetDisplayAmount.textContent = formatCurrency(budget, settings.currency);
            const periodExpenses = filterExpensesByPeriod(expenses, timePeriod);
            let spent = 0;
            periodExpenses.forEach(exp => {
                const v = convertAmount(exp.amount, exp.currency, settings.currency);
                spent += v !== null ? v : exp.amount;
            });
            budgetSpentAmount.textContent     = formatCurrency(spent, settings.currency);
            budgetRemainingAmount.textContent = formatCurrency(budget - spent, settings.currency);

            const pct = Math.min(100, Math.max(0, (spent / budget) * 100));
            budgetProgressFill.style.width = `${pct}%`;
            // Change bar color on overspend
            budgetProgressFill.style.background = pct >= 100
                ? 'var(--accent-danger)'
                : pct >= 80
                    ? 'var(--accent-warning)'
                    : 'var(--accent-success)';

            if (spent > budget) {
                budgetWarning.textContent = `Budget exceeded by ${formatCurrency(spent - budget, settings.currency)}`;
                budgetWarning.classList.remove('hidden');
            } else {
                budgetWarning.classList.add('hidden');
            }
        } else {
            budgetDisplayAmount.textContent   = '-';
            budgetSpentAmount.textContent     = '-';
            budgetRemainingAmount.textContent = '-';
            budgetProgressFill.style.width    = '0%';
            budgetWarning.classList.add('hidden');
        }
    }

    function updatePeriodTotal() {
        const periodExpenses = filterExpensesByPeriod(expenses, timePeriod);
        let total = 0;
        periodExpenses.forEach(exp => {
            const v = convertAmount(exp.amount, exp.currency, settings.currency);
            total += v !== null ? v : exp.amount;
        });
        periodTotalAmount.textContent = formatCurrency(total, settings.currency);
    }

    // =====================================================
    //  EXPENSES TABLE
    // =====================================================
    function renderExpensesTable() {
        const filtered = getFilteredExpenses();
        const sorted   = [...filtered].sort((a, b) => new Date(b.date) - new Date(a.date));

        expensesTableBody.innerHTML = '';

        if (sorted.length === 0) {
            const row = document.createElement('tr');
            row.className = 'empty-row';
            row.innerHTML = `<td colspan="6">No expenses match the current filters.</td>`;
            expensesTableBody.appendChild(row);
            return;
        }

        sorted.forEach(expense => {
            const converted     = convertAmount(expense.amount, expense.currency, settings.currency);
            const isSame        = expense.currency === settings.currency;
            const convertedText = converted !== null ? formatCurrency(converted, settings.currency) : '-';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${formatDisplayDate(expense.date)}</td>
                <td><span class="cat-pill">${escapeHtml(expense.category)}</span></td>
                <td style="color:var(--text-secondary)">${escapeHtml(expense.note) || '-'}</td>
                <td>${formatCurrency(expense.amount, expense.currency)}</td>
                <td class="converted-amount ${isSame ? 'same-currency' : ''}">${isSame ? '-' : convertedText}</td>
                <td class="action-cell">
                    <button class="edit-btn" data-id="${expense.id}" title="Edit" aria-label="Edit"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg> Edit</button>
                    <button class="action-btn" data-id="${expense.id}" title="Delete" aria-label="Delete"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg> Delete</button>
                </td>
            `;
            expensesTableBody.appendChild(row);
        });

        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', e => deleteExpense(e.currentTarget.getAttribute('data-id')));
        });
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', e => {
                const id = e.currentTarget.getAttribute('data-id');
                const expense = expenses.find(exp => exp.id === id);
                if (expense) openEditModal(expense);
            });
        });
    }

    // =====================================================
    //  EDIT EXPENSE MODAL
    // =====================================================
    function openEditModal(expense) {
        editExpenseIdInput.value    = expense.id;
        editAmountInput.value       = expense.amount;
        editCategorySelect.value    = expense.category;
        editDateInput.value         = expense.date;
        editNoteInput.value         = expense.note || '';

        // Show currency of the original expense
        const currencyInfo = CURRENCIES[expense.currency];
        if (currencyInfo) {
            editAmountCurrencyLabel.textContent  = `(${expense.currency})`;
            editCurrencySymbolPrefix.textContent = currencyInfo.symbol;
        }

        editExpenseModal.classList.remove('hidden');
        editAmountInput.focus();
    }

    function closeEditModal() {
        editExpenseModal.classList.add('hidden');
        editExpenseForm.reset();
    }

    async function updateExpense(id, updatedData) {
        const original = expenses.find(exp => exp.id === id);
        if (!original) return;
        const payload = { ...original, ...updatedData };
        try {
            const res = await fetch(`${API_BASE}/${encodeURIComponent(id)}`, {
                method:  'PUT',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify(payload)
            });
            const data = await parseApiResponse(res);
            if (!res.ok || !data.success) throw new Error(data.error || 'API error');
            // Update local array
            const index = expenses.findIndex(exp => exp.id === id);
            if (index !== -1) expenses[index] = data.expense;
            updateAll();
            showToast('Expense updated successfully.', 'success');
            closeEditModal();
        } catch (e) {
            console.error('[updateExpense]', e);
            showToast('Failed to update expense: ' + e.message, 'error');
        }
    }

    // =====================================================
    //  CHART
    // =====================================================
    const CHART_COLORS = [
        '#2563eb', '#0284c7', '#059669', '#d97706', '#475569',
        '#0d9488', '#ea580c', '#0891b2', '#64748b', '#ca8a04'
    ];

    function renderChart() {
        const filtered    = getFilteredExpenses();
        const toCurrency  = settings.currency;
        const selCategory = categoryFilter.value;   // '' = All Categories
        const selMonth    = monthFilter.value;       // '' = All Months

        // Decide the view mode:
        //   daily  → a month is selected (drill-down by date)
        //   normal → no month selected  (group by category as before)
        const isDailyView = selMonth !== '';

        let labels = [], data = [], chartTitle = '';

        if (currentChartType === 'line') {
            // Line chart always groups by date (existing behaviour)
            const dateTotals = {};
            filtered.forEach(exp => {
                const val = convertAmount(exp.amount, exp.currency, toCurrency) ?? exp.amount;
                dateTotals[exp.date] = (dateTotals[exp.date] || 0) + val;
            });
            const sortedDates = Object.keys(dateTotals).sort();
            labels = sortedDates.map(formatDisplayDate);
            data   = sortedDates.map(d => dateTotals[d]);
            chartTitle = 'Spending by Date';

        } else if (isDailyView) {
            // Bar / Pie / Doughnut with a month selected → daily breakdown
            const dateTotals = {};
            filtered.forEach(exp => {
                const val = convertAmount(exp.amount, exp.currency, toCurrency) ?? exp.amount;
                dateTotals[exp.date] = (dateTotals[exp.date] || 0) + val;
            });
            const sortedDates = Object.keys(dateTotals).sort();
            labels = sortedDates.map(formatDisplayDate);
            data   = sortedDates.map(d => dateTotals[d]);

            // Build a human-readable month label, e.g. "September 2026"
            const monthLabel = new Date(selMonth + '-02')
                .toLocaleString(undefined, { year: 'numeric', month: 'long' });
            chartTitle = selCategory
                ? `${selCategory} Spending \u2014 ${monthLabel} (Daily)`
                : `All Spending \u2014 ${monthLabel} (Daily)`;

        } else {
            // Default: group by category (existing behaviour)
            const catTotals = {};
            filtered.forEach(exp => {
                const val = convertAmount(exp.amount, exp.currency, toCurrency) ?? exp.amount;
                catTotals[exp.category] = (catTotals[exp.category] || 0) + val;
            });
            labels = Object.keys(catTotals);
            data   = Object.values(catTotals);
            chartTitle = selCategory
                ? `Spending \u2014 ${selCategory}`
                : 'Spending by Category';
        }

        if (chartInstance) { chartInstance.destroy(); chartInstance = null; }

        // Only hide the chart when there are genuinely no matching expenses,
        // NOT when a single category is filtered (1 label is fine to render).
        if (filtered.length === 0) {
            chartCanvas.style.display = 'none';
            noChartMsg.classList.remove('hidden');
            return;
        }
        chartCanvas.style.display = 'block';
        noChartMsg.classList.add('hidden');

        const isMultiColor = currentChartType === 'pie' || currentChartType === 'doughnut';
        const ctx = chartCanvas.getContext('2d');
        chartInstance = new Chart(ctx, {
            type: currentChartType,
            data: {
                labels,
                datasets: [{
                    label: `Spending (${toCurrency})`,
                    data,
                    backgroundColor: isMultiColor ? CHART_COLORS : 'rgba(99,102,241,0.7)',
                    borderColor:     isMultiColor ? CHART_COLORS : 'rgba(99,102,241,1)',
                    borderWidth: 2,
                    borderRadius: currentChartType === 'bar' ? 6 : 0,
                    fill: currentChartType === 'line',
                    tension: 0.4,
                    pointBackgroundColor: '#6366f1',
                    pointRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: isMultiColor,
                        labels: { color: '#64748b', font: { family: 'Inter', size: 12 } }
                    },
                    title: {
                        display: true,
                        text: chartTitle,
                        color: '#1e293b',
                        font: { family: 'Inter', size: 14, weight: '600' }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30,41,59,0.95)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(99,102,241,0.4)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: ctx => {
                                const v = typeof ctx.parsed.y !== 'undefined' ? ctx.parsed.y : ctx.parsed;
                                return `  ${formatCurrency(v, toCurrency)}`;
                            }
                        }
                    }
                },
                scales: isMultiColor ? {} : {
                    x: {
                        grid:  { color: 'rgba(0,0,0,0.06)' },
                        ticks: { color: '#64748b', font: { family: 'Inter' } }
                    },
                    y: {
                        beginAtZero: true,
                        grid:  { color: 'rgba(0,0,0,0.06)' },
                        ticks: {
                            color: '#64748b',
                            font: { family: 'Inter' },
                            callback: v => formatCurrency(v, toCurrency)
                        }
                    }
                }
            }
        });
    }

    // =====================================================
    //  EXPENSE CRUD
    // =====================================================
    async function addExpense(expense) {
        try {
            const res = await fetch(API_BASE, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify(expense)
            });
            const data = await parseApiResponse(res);
            if (!res.ok || !data.success) throw new Error(data.error || 'API error');
            expenses.push(data.expense);
            updateAll();
        } catch (e) {
            console.error('[addExpense]', e);
            showToast('Failed to save expense: ' + e.message, 'error');
        }
    }

    function deleteExpense(id) {
        // Find the expense for the preview
        const expense = expenses.find(e => e.id === id);
        if (!expense) return;

        // Build a human-readable preview
        const converted = convertAmount(expense.amount, expense.currency, settings.currency);
        const amountStr = formatCurrency(expense.amount, expense.currency);
        const convertedStr = (converted !== null && expense.currency !== settings.currency)
            ? ` &rarr; ${formatCurrency(converted, settings.currency)}`
            : '';

        deleteExpensePreview.innerHTML = `
            <strong>${escapeHtml(expense.category)}</strong> - ${formatDisplayDate(expense.date)}<br>
            <strong>${amountStr}</strong>${convertedStr}
            ${expense.note ? `<br><span style="color:var(--text-secondary)">${escapeHtml(expense.note)}</span>` : ''}
        `;

        pendingDeleteId = id;
        deleteConfirmModal.classList.remove('hidden');
    }

    async function confirmDelete() {
        if (!pendingDeleteId) return;
        const idToDelete = pendingDeleteId;
        closeDeleteModal();
        try {
            const res = await fetch(`${API_BASE}/${encodeURIComponent(idToDelete)}`, {
                method: 'DELETE'
            });
            const data = await parseApiResponse(res);
            if (!res.ok || !data.success) throw new Error(data.error || 'API error');
            expenses = expenses.filter(e => e.id !== idToDelete);
            updateAll();
            showToast('Expense deleted.', 'info', 2500);
        } catch (e) {
            console.error('[confirmDelete]', e);
            showToast('Failed to delete expense: ' + e.message, 'error');
        }
    }

    function closeDeleteModal() {
        deleteConfirmModal.classList.add('hidden');
        pendingDeleteId = null;
        deleteExpensePreview.innerHTML = '';
    }

    function updateAll() {
        renderDashboard();
        renderExpensesTable();
        populateCategories();
        populateMonthFilter();
        renderChart();
        updateBudgetUI();
        updatePeriodTotal();
        updateExtendedDashboard();
    }

    // =====================================================
    //  CSV EXPORT - Professional (UTF-8 BOM, converted column)
    // =====================================================
    function exportCSV() {
        if (expenses.length === 0) {
            showToast('No expenses to export.', 'warning');
            return;
        }
        const BOM = '\uFEFF';
        const cur = settings.currency;
        const headerRow = ['Date', 'Category', 'Amount', 'Currency', 'Note',
            `Converted Amount (${cur})`, 'Converted Currency'];

        const rows = expenses.map(exp => {
            const converted = convertAmount(exp.amount, exp.currency, cur);
            return [
                exp.date, exp.category,
                exp.amount.toFixed(2), exp.currency,
                exp.note || '',
                converted !== null && exp.currency !== cur ? converted.toFixed(2) : '',
                converted !== null && exp.currency !== cur ? cur : ''
            ];
        });

        const csv = BOM + [headerRow, ...rows]
            .map(row => row.map(v => escapeCSVField(String(v ?? ''))).join(','))
            .join('\r\n');

        downloadBlob(csv, `expenses_${todayString()}.csv`, 'text/csv;charset=utf-8;');
        showToast(`Exported ${expenses.length} expense${expenses.length !== 1 ? 's' : ''}`, 'success');
    }

    // =====================================================
    //  REPORT EXPORT
    // =====================================================
    function exportReportCSV() {
        if (expenses.length === 0) {
            showToast('No expenses to report on.', 'warning');
            return;
        }
        const BOM = '\uFEFF';
        const advanced    = calculateAdvancedExpenses(expenses);
        const periodTotal = filterExpensesByPeriod(expenses, timePeriod).reduce((sum, exp) => {
            const v = convertAmount(exp.amount, exp.currency, settings.currency);
            return sum + (v !== null ? v : exp.amount);
        }, 0);

        const headers = ['Metric', 'Period', 'Amount', 'Currency'];
        const rows = [
            ['Total Spending',              'All Time',     advanced.total.toFixed(2),    settings.currency],
            ['Monthly Spending',            'Current Month',advanced.monthly.toFixed(2),  settings.currency],
            ['Weekly Spending',             'Current Week', advanced.weekly.toFixed(2),   settings.currency],
            ['Average per Expense',         'All Time',     advanced.average.toFixed(2),  settings.currency],
            ['Highest Single Expense',      'All Time',     advanced.highest.toFixed(2),  settings.currency],
            ['Lowest Single Expense',       'All Time',     advanced.lowest.toFixed(2),   settings.currency],
            ['Total Number of Expenses',    'All Time',     advanced.count.toString(),    ''],
            ['Top Spending Category',        'All Time',     advanced.highestCategory,     ''],
            ['', '', '', ''],
            ['--- Category Breakdown ---',  '', '', ''],
            ...Object.entries(advanced.categoryTotals).map(([cat, amt]) => [cat, 'All Time', amt.toFixed(2), settings.currency]),
            ['', '', '', ''],
            [`Period Total (${timePeriod})`, 'Current Period', periodTotal.toFixed(2), settings.currency],
        ];
        if (budget > 0) {
            const spent     = filterExpensesByPeriod(expenses, 'monthly').reduce((s, exp) => {
                const v = convertAmount(exp.amount, exp.currency, settings.currency);
                return s + (v !== null ? v : exp.amount);
            }, 0);
            rows.push(['Monthly Budget',  'Current Month', budget.toFixed(2),            settings.currency]);
            rows.push(['Budget Remaining','Current Month', (budget - spent).toFixed(2),  settings.currency]);
        }

        const csv = BOM + [headers, ...rows]
            .map(row => row.map(v => escapeCSVField(String(v ?? ''))).join(','))
            .join('\r\n');

        downloadBlob(csv, `report_${todayString()}.csv`, 'text/csv;charset=utf-8;');
        showToast('Report exported successfully', 'success');
    }

    function escapeCSVField(value) {
        if (value.includes('"') || value.includes(',') || value.includes('\n') || value.includes('\r')) {
            return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
    }

    function todayString() {
        const now = new Date();
        return `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
    }

    function downloadBlob(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url  = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href  = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    // =====================================================
    //  BACKUP / RESTORE  (JSON - preserves all data)
    // =====================================================
    function backupJSON() {
        if (expenses.length === 0 && budget === 0) {
            showToast('Nothing to backup yet. Add some expenses first.', 'warning');
            return;
        }
        const payload = {
            version   : 1,
            exportedAt: new Date().toISOString(),
            settings,
            budget,
            expenses,
        };
        const json = JSON.stringify(payload, null, 2);
        downloadBlob(json, `expenseiq_backup_${todayString()}.json`, 'application/json');
        showToast(`Backup saved successfully (${expenses.length} record${expenses.length !== 1 ? 's' : ''})`, 'success');
    }

    function restoreJSON(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.name.endsWith('.json')) {
            showToast('Please select a valid .json backup file.', 'error');
            event.target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = async e => {
            try {
                const payload = JSON.parse(e.target.result);

                // Basic structure validation
                if (!payload.version || !Array.isArray(payload.expenses)) {
                    throw new Error('Unrecognised backup format.');
                }

                // Validate each expense entry
                const valid = [];
                const skipped = [];
                payload.expenses.forEach((exp, i) => {
                    if (
                        exp.id && exp.date && exp.category &&
                        typeof exp.amount === 'number' && exp.amount > 0 &&
                        exp.currency && CURRENCIES[exp.currency]
                    ) {
                        valid.push(exp);
                    } else {
                        skipped.push(`Row ${i + 1}`);
                    }
                });

                if (valid.length === 0) {
                    showToast('No valid expenses found in this backup.', 'error');
                    event.target.value = '';
                    return;
                }

                // Restore expenses via backend bulk replace
                try {
                    const res = await fetch(API_BASE + '/bulk', {
                        method:  'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body:    JSON.stringify({ expenses: valid, mode: 'replace' })
                    });
                    const bulkData = await parseApiResponse(res);
                    if (!res.ok || !bulkData.success) throw new Error(bulkData.error || 'Bulk API error');
                    expenses = valid;
                } catch (apiErr) {
                    console.error('[restoreJSON] API error:', apiErr);
                    showToast('Restore to CSV failed: ' + apiErr.message, 'error');
                    event.target.value = '';
                    return;
                }

                // Restore settings if present
                if (payload.settings && CURRENCIES[payload.settings.currency]) {
                    settings = payload.settings;
                    saveSettings();
                    populateCurrencySelector();
                    currencySelect.value = settings.currency;
                    updateCurrencyUI();
                }

                // Restore budget if present
                if (typeof payload.budget === 'number' && payload.budget >= 0) {
                    budget = payload.budget;
                    saveBudget();
                    if (budget > 0) budgetAmountInput.value = budget;
                }

                updateAll();

                const msg = skipped.length > 0
                    ? `Restored ${valid.length} expense(s). Skipped ${skipped.length} invalid.`
                    : `Restored ${valid.length} expense(s) from backup`;
                showToast(msg, skipped.length > 0 ? 'warning' : 'success', 6000);

            } catch (err) {
                showToast(`Restore failed: ${err.message}`, 'error', 7000);
            }
            event.target.value = '';
        };
        reader.onerror = () => {
            showToast('Failed to read backup file.', 'error');
            event.target.value = '';
        };
        reader.readAsText(file, 'UTF-8');
    }


    // =====================================================
    //  CSV IMPORT - RFC 4180-compliant parser
    // =====================================================
    function importCSV(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.name.endsWith('.csv')) {
            showToast('Please select a valid .csv file.', 'error');
            event.target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = async e => {
            const text  = e.target.result.replace(/^\uFEFF/, '');
            const lines = parseCSVLines(text);

            if (lines.length < 2) {
                showToast('CSV file is empty or has no data rows.', 'error');
                event.target.value = '';
                return;
            }

            const header = lines[0].map(h => h.trim().toLowerCase().replace(/\s+/g, '_'));
            const idx = {
                date:     header.findIndex(h => h === 'date'),
                category: header.findIndex(h => h === 'category'),
                amount:   header.findIndex(h => h === 'amount'),
                currency: header.findIndex(h => h === 'currency'),
                note:     header.findIndex(h => h.includes('note')),
            };

            if (idx.date === -1 || idx.category === -1 || idx.amount === -1) {
                showToast('CSV must have at least: date, category, amount columns.', 'error', 7000);
                event.target.value = '';
                return;
            }

            const imported = [], skipped = [];
            for (let i = 1; i < lines.length; i++) {
                const cols = lines[i];
                if (cols.every(c => c.trim() === '')) continue;

                const dateVal     = (cols[idx.date]     || '').trim();
                const categoryVal = (cols[idx.category] || '').trim();
                const amountRaw   = (cols[idx.amount]   || '').trim();
                const currencyVal = (idx.currency !== -1 ? cols[idx.currency] || '' : '').trim().toUpperCase() || settings.currency;
                const noteVal     = (idx.note !== -1    ? cols[idx.note]    || '' : '').trim();
                const amountVal   = parseFloat(amountRaw);

                let valid = true, reason = '';
                if (!dateVal || !/^\d{4}-\d{2}-\d{2}$/.test(dateVal)) {
                    valid = false; reason = `Row ${i+1}: Invalid date "${dateVal}" (expected YYYY-MM-DD)`;
                } else if (!categoryVal) {
                    valid = false; reason = `Row ${i+1}: Category is required`;
                } else if (isNaN(amountVal) || amountVal <= 0) {
                    valid = false; reason = `Row ${i+1}: Invalid amount "${amountRaw}"`;
                } else if (!CURRENCIES[currencyVal]) {
                    valid = false; reason = `Row ${i+1}: Unknown currency "${currencyVal}"`;
                }

                if (valid) {
                    imported.push({
                        id: `import_${Date.now()}_${i}_${Math.random().toString(36).slice(2)}`,
                        amount: amountVal, currency: currencyVal,
                        category: categoryVal, date: dateVal, note: noteVal
                    });
                } else {
                    skipped.push(reason);
                }
            }

            if (imported.length > 0) {
                // Push to backend with merge mode (preserve existing + add new)
                try {
                    const res = await fetch(API_BASE + '/bulk', {
                        method:  'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body:    JSON.stringify({ expenses: imported, mode: 'merge' })
                    });
                    const data = await parseApiResponse(res);
                    if (!res.ok || !data.success) throw new Error(data.error || 'Bulk API error');
                    // Reload from backend so local state is consistent
                    const reload = await fetch(API_BASE);
                    const reloadData = await parseApiResponse(reload);
                    if (reloadData.success) expenses = reloadData.expenses;
                    else imported.forEach(exp => expenses.push(exp));
                    updateAll();
                    const msg = skipped.length > 0
                        ? `Imported ${imported.length} row(s). Skipped ${skipped.length} invalid.`
                        : `Successfully imported ${imported.length} expense${imported.length !== 1 ? 's' : ''}`;
                    showToast(msg, skipped.length > 0 ? 'warning' : 'success', 6000);
                } catch (apiErr) {
                    console.error('[importCSV] API error:', apiErr);
                    showToast('Import failed: ' + apiErr.message, 'error');
                }
            } else {
                showToast(`No valid expenses found. ${skipped.length} row(s) skipped.`, 'error', 7000);
            }
            if (skipped.length > 0) console.warn('Skipped CSV rows:', skipped);
            event.target.value = '';
        };
        reader.onerror = () => {
            showToast('Failed to read file. Please try again.', 'error');
            event.target.value = '';
        };
        reader.readAsText(file, 'UTF-8');
    }

    /** RFC 4180-compliant CSV parser */
    function parseCSVLines(text) {
        const rows = [];
        let row = [], field = '', inQuotes = false, i = 0;
        while (i < text.length) {
            const ch = text[i];
            if (inQuotes) {
                if (ch === '"') {
                    if (text[i + 1] === '"') { field += '"'; i += 2; }
                    else { inQuotes = false; i++; }
                } else { field += ch; i++; }
            } else {
                if      (ch === '"')                       { inQuotes = true; i++; }
                else if (ch === ',')                       { row.push(field); field = ''; i++; }
                else if (ch === '\r' && text[i+1] === '\n') { row.push(field); rows.push(row); row = []; field = ''; i += 2; }
                else if (ch === '\n')                      { row.push(field); rows.push(row); row = []; field = ''; i++; }
                else                                       { field += ch; i++; }
            }
        }
        if (field !== '' || row.length > 0) { row.push(field); rows.push(row); }
        return rows.filter(r => r.some(c => c.trim() !== ''));
    }

    // =====================================================
    //  EVENT LISTENERS
    // =====================================================
    function addEventListeners() {
        // Currency dropdown
        currencySelect.addEventListener('change', async e => {
            const newCurrency = e.target.value;
            if (newCurrency === settings.currency) return;
            settings.currency = newCurrency;
            saveSettings();
            updateCurrencyUI();
            // Show loading in exchange info immediately
            exchangeRateDisplay.textContent = 'Loading rate…';
            exchangeInfoEl.classList.remove('hidden');
            showToast(`Currency changed to ${newCurrency}. Fetching live rates…`, 'info', 3000);
            await fetchExchangeRates();
            updateAll();
        });

        // Chart type tabs
        chartTypeTabs.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                chartTypeTabs.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentChartType = btn.getAttribute('data-type');
                renderChart();
            });
        });

        // Add expense form - category dropdown: show/hide custom input
        const categorySelect   = document.getElementById('category');
        const customCategoryRow = document.getElementById('custom-category-row');
        const customCategoryInput = document.getElementById('custom-category');

        categorySelect.addEventListener('change', () => {
            if (categorySelect.value === 'Other') {
                customCategoryRow.style.display = '';
                customCategoryInput.focus();
            } else {
                customCategoryRow.style.display = 'none';
                customCategoryInput.value = '';
            }
        });

        // Add expense form
        form.addEventListener('submit', e => {
            e.preventDefault();
            const amount   = parseFloat(document.getElementById('amount').value);
            const rawCat   = categorySelect.value;
            const date     = document.getElementById('date').value;
            const note     = document.getElementById('note').value.trim();

            if (!amount || amount <= 0) { showToast('Enter a valid amount > 0.', 'error'); return; }
            if (!rawCat)               { showToast('Please select a category.', 'error'); return; }
            if (!date)                 { showToast('Please select a date.', 'error'); return; }

            // Resolve final category name
            let category = rawCat;
            if (rawCat === 'Other') {
                const custom = customCategoryInput.value.trim();
                if (!custom) {
                    showToast('Please enter a custom category name.', 'error');
                    customCategoryInput.focus();
                    return;
                }
                category = custom;
            }

            addExpense({
                id: Date.now().toString() + Math.random().toString(36).slice(2),
                amount, currency: settings.currency, category, date, note: note || ''
            });

            form.reset();
            customCategoryRow.style.display = 'none';
            customCategoryInput.value = '';
            document.getElementById('date').value = new Date().toISOString().slice(0, 10);
            showToast(`Added: ${formatCurrency(amount, settings.currency)} for ${category}`, 'success');
        });

        // Edit expense form
        editExpenseForm.addEventListener('submit', e => {
            e.preventDefault();
            const id       = editExpenseIdInput.value;
            const amount   = parseFloat(editAmountInput.value);
            const category = editCategorySelect.value;
            const date     = editDateInput.value;
            const note     = editNoteInput.value.trim();

            if (!amount || amount <= 0) { showToast('Enter a valid amount > 0.', 'error'); return; }
            if (!category)              { showToast('Please select a category.', 'error'); return; }
            if (!date)                  { showToast('Please select a date.', 'error'); return; }

            // Keep original currency (editing amount in same currency as it was added)
            const originalExpense = expenses.find(exp => exp.id === id);
            updateExpense(id, {
                amount, category, date, note,
                currency: originalExpense?.currency || settings.currency
            });
        });

        // Edit modal close buttons
        editModalCloseBtn.addEventListener('click', closeEditModal);
        editCancelBtn.addEventListener('click', closeEditModal);

        // Close modal on backdrop click
        editExpenseModal.addEventListener('click', e => {
            if (e.target === editExpenseModal) closeEditModal();
        });

        // Escape key closes modal
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && !editExpenseModal.classList.contains('hidden')) closeEditModal();
        });

        // Filters
        searchInput.addEventListener('input', updateAll);
        categoryFilter.addEventListener('change', updateAll);
        monthFilter.addEventListener('change', updateAll);

        // Time period tabs
        periodTabs.forEach(btn => {
            btn.addEventListener('click', () => {
                periodTabs.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                timePeriod = btn.getAttribute('data-period');
                updateBudgetUI();
                updatePeriodTotal();
            });
        });

        // Budget input (debounced)
        let budgetTimer;
        budgetAmountInput.addEventListener('input', () => {
            clearTimeout(budgetTimer);
            budgetTimer = setTimeout(() => {
                const val = parseFloat(budgetAmountInput.value);
                budget = isNaN(val) || val < 0 ? 0 : val;
                saveBudget();
                updateBudgetUI();
                updateExtendedDashboard();
                if (budget > 0) showToast(`Budget set to ${formatCurrency(budget, settings.currency)}`, 'success', 2000);
            }, 600);
        });

        // CSV buttons
        exportCsvBtn.addEventListener('click', exportCSV);
        exportReportBtn.addEventListener('click', exportReportCSV);
        csvFileInput.addEventListener('change', importCSV);

        // Delete confirmation modal
        deleteConfirmBtn.addEventListener('click', confirmDelete);
        deleteCancelBtn.addEventListener('click', closeDeleteModal);
        deleteModalCloseBtn.addEventListener('click', closeDeleteModal);
        deleteConfirmModal.addEventListener('click', e => {
            if (e.target === deleteConfirmModal) closeDeleteModal();
        });
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && !deleteConfirmModal.classList.contains('hidden')) closeDeleteModal();
        });

        // Backup / Restore JSON
        backupJsonBtn.addEventListener('click', backupJSON);
        restoreJsonInput.addEventListener('change', restoreJSON);
    }

    // =====================================================
    //  INIT
    // =====================================================
    async function init() {
        loadSettings();
        loadBudget();
        populateCurrencySelector();
        currencySelect.value = settings.currency;
        updateCurrencyUI();
        addEventListeners();

        document.getElementById('date').value = new Date().toISOString().slice(0, 10);

        // Load expenses from CSV backend first, then render UI
        await loadExpenses();

        populateCategories();
        populateMonthFilter();
        renderDashboard();
        renderExpensesTable();
        renderChart();
        updateBudgetUI();
        updatePeriodTotal();
        updateExtendedDashboard();

        // Fetch live exchange rates and re-render with converted values
        await fetchExchangeRates();
        renderDashboard();
        renderExpensesTable();
        renderChart();
        updateBudgetUI();
        updatePeriodTotal();
        updateExtendedDashboard();
    }

    init();
});