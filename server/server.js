'use strict';

const express = require('express');
const path    = require('path');
const fs      = require('fs');
const os      = require('os');

// ─── Environment & Paths ───────────────────────────────────────────────────────
const ROOT_DIR = path.join(__dirname, '..');
const LOCAL_DATA_DIR = path.join(ROOT_DIR, 'data');
const LOCAL_CSV_PATH = path.join(LOCAL_DATA_DIR, 'expenses.csv');

// Detect serverless environment (Vercel, AWS Lambda)
const isServerless = Boolean(
    process.env.VERCEL ||
    process.env.AWS_LAMBDA_FUNCTION_NAME ||
    process.env.LAMBDA_TASK_ROOT
);

function resolveStorage() {
    if (isServerless) {
        const tmpDir = os.tmpdir();
        return {
            dir: tmpDir,
            path: path.join(tmpDir, 'expenses.csv'),
            isServerless: true
        };
    }
    return {
        dir: LOCAL_DATA_DIR,
        path: LOCAL_CSV_PATH,
        isServerless: false
    };
}

const CSV_FIELDS = ['id', 'date', 'amount', 'currency', 'category', 'note'];
const CSV_HEADER = CSV_FIELDS.join(',');

// In-memory fallback and performance cache
let memoryExpenses = null;

// ─── Ensure data directory + CSV exists ────────────────────────────────────────
function ensureDataDir() {
    const storage = resolveStorage();
    try {
        if (!fs.existsSync(storage.dir)) {
            fs.mkdirSync(storage.dir, { recursive: true });
        }
        if (!fs.existsSync(storage.path)) {
            // Seed from bundled repository CSV if available
            if (fs.existsSync(LOCAL_CSV_PATH)) {
                try {
                    const seed = fs.readFileSync(LOCAL_CSV_PATH, 'utf8');
                    fs.writeFileSync(storage.path, seed, 'utf8');
                } catch {
                    fs.writeFileSync(storage.path, CSV_HEADER + '\r\n', 'utf8');
                }
            } else {
                fs.writeFileSync(storage.path, CSV_HEADER + '\r\n', 'utf8');
            }
        }
    } catch (err) {
        console.warn('[CSV Storage] Notice on directory check:', err.message);
        if (memoryExpenses === null) {
            memoryExpenses = [];
        }
    }
}
ensureDataDir();

// ─── CSV helpers ───────────────────────────────────────────────────────────────

function csvEscape(value) {
    const str = String(value == null ? '' : value);
    if (str.includes('"') || str.includes(',') || str.includes('\n') || str.includes('\r')) {
        return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
}

function parseCsvLine(line) {
    const fields = [];
    let field = '', inQuotes = false, i = 0;
    while (i < line.length) {
        const ch = line[i];
        if (inQuotes) {
            if (ch === '"') {
                if (line[i + 1] === '"') { field += '"'; i += 2; }
                else { inQuotes = false; i++; }
            } else { field += ch; i++; }
        } else {
            if      (ch === '"') { inQuotes = true; i++; }
            else if (ch === ',') { fields.push(field); field = ''; i++; }
            else                 { field += ch; i++; }
        }
    }
    fields.push(field);
    return fields;
}

function readAllExpenses() {
    ensureDataDir();
    const storage = resolveStorage();
    let raw;
    try {
        raw = fs.readFileSync(storage.path, 'utf8');
    } catch (err) {
        if (memoryExpenses !== null) return memoryExpenses;
        try {
            if (fs.existsSync(LOCAL_CSV_PATH)) {
                raw = fs.readFileSync(LOCAL_CSV_PATH, 'utf8');
            } else {
                return [];
            }
        } catch {
            return [];
        }
    }

    // Strip UTF-8 BOM
    if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);

    const lines = raw.split(/\r?\n/).filter(l => l.trim() !== '');
    if (lines.length < 2) {
        return memoryExpenses || [];
    }

    const header = parseCsvLine(lines[0]).map(h => h.trim().toLowerCase());
    const idx = {};
    CSV_FIELDS.forEach(f => { idx[f] = header.indexOf(f); });

    const expenses = [];
    for (let i = 1; i < lines.length; i++) {
        const cols      = parseCsvLine(lines[i]);
        const id        = idx.id       >= 0 ? (cols[idx.id]       || '').trim() : '';
        const date      = idx.date     >= 0 ? (cols[idx.date]     || '').trim() : '';
        const amountRaw = idx.amount   >= 0 ? (cols[idx.amount]   || '').trim() : '';
        const currency  = idx.currency >= 0 ? (cols[idx.currency] || '').trim() : 'INR';
        const category  = idx.category >= 0 ? (cols[idx.category] || '').trim() : '';
        const note      = idx.note     >= 0 ? (cols[idx.note]     || '').trim() : '';

        const amount = parseFloat(amountRaw);
        if (!id || !date || isNaN(amount) || amount <= 0 || !category) continue;

        expenses.push({ id, date, amount, currency: currency || 'INR', category, note: note || '' });
    }
    memoryExpenses = expenses;
    return expenses;
}

// Serial write-lock to prevent concurrent CSV corruption
let writeLock = Promise.resolve();

function writeAllExpenses(expenses) {
    writeLock = writeLock
        .then(() => _doWrite(expenses))
        .catch(err => console.error('[CSV] Write lock error:', err.message));
    return writeLock;
}

function _doWrite(expenses) {
    return new Promise((resolve) => {
        memoryExpenses = [...expenses];
        ensureDataDir();
        const storage = resolveStorage();
        const tmpPath = storage.path + '.tmp';
        const lines = [CSV_HEADER];
        for (const exp of expenses) {
            lines.push([
                csvEscape(exp.id),
                csvEscape(exp.date),
                csvEscape(exp.amount),
                csvEscape(exp.currency),
                csvEscape(exp.category),
                csvEscape(exp.note || '')
            ].join(','));
        }
        const content = lines.join('\r\n') + '\r\n';
        try {
            fs.writeFileSync(tmpPath, content, 'utf8');
            fs.renameSync(tmpPath, storage.path);  // atomic replace
            resolve();
        } catch (err) {
            console.warn('[CSV] Disk write notice, using memory cache:', err.message);
            resolve();
        }
    });
}

// ─── Validation ───────────────────────────────────────────────────────────────
const VALID_CURRENCIES = new Set([
    'INR','USD','EUR','GBP','JPY','CNY','AUD','CAD','SGD','AED','SAR','QAR',
    'KWD','CHF','NZD','ZAR','BRL','MXN','KRW','THB','MYR','IDR','PHP','HKD',
    'TRY','SEK','NOK','DKK','PLN','RUB'
]);

function validateExpense(body) {
    const errors = [];
    if (!body || typeof body !== 'object') {
        return ['Invalid request body'];
    }
    if (!body.id || typeof body.id !== 'string' || !body.id.trim())
        errors.push('id is required');
    if (!body.date || !/^\d{4}-\d{2}-\d{2}$/.test(body.date))
        errors.push('date must be YYYY-MM-DD');
    const amount = parseFloat(body.amount);
    if (isNaN(amount) || amount <= 0)
        errors.push('amount must be a positive number');
    if (!body.currency || !VALID_CURRENCIES.has(body.currency))
        errors.push('invalid or missing currency');
    if (!body.category || typeof body.category !== 'string' || !body.category.trim())
        errors.push('category is required');
    return errors;
}

// ─── Express Application ───────────────────────────────────────────────────────
const app = express();
app.use(express.json());

// Serve static frontend when running locally
app.use(express.static(ROOT_DIR, { index: 'index.html' }));

// ─── Expenses Router ───────────────────────────────────────────────────────────
const expensesRouter = express.Router();

// GET /api/expenses
expensesRouter.get('/', (req, res) => {
    try {
        const expenses = readAllExpenses();
        res.json({ success: true, expenses });
    } catch (err) {
        console.error('[GET /expenses]', err.message);
        res.status(500).json({ success: false, error: 'Failed to read expenses' });
    }
});

// GET /api/expenses/export — returns raw CSV as download
expensesRouter.get('/export', (req, res) => {
    try {
        const storage = resolveStorage();
        let content;
        if (fs.existsSync(storage.path)) {
            content = fs.readFileSync(storage.path, 'utf8');
        } else {
            const current = readAllExpenses();
            const lines = [CSV_HEADER];
            for (const exp of current) {
                lines.push([
                    csvEscape(exp.id),
                    csvEscape(exp.date),
                    csvEscape(exp.amount),
                    csvEscape(exp.currency),
                    csvEscape(exp.category),
                    csvEscape(exp.note || '')
                ].join(','));
            }
            content = lines.join('\r\n') + '\r\n';
        }
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', 'attachment; filename="expenses.csv"');
        res.send(content);
    } catch (err) {
        res.status(500).json({ success: false, error: 'Failed to read CSV' });
    }
});

// POST /api/expenses/bulk — declared BEFORE generic POST to avoid route conflict
expensesRouter.post('/bulk', async (req, res) => {
    const { expenses: incoming, mode = 'replace' } = req.body || {};
    if (!Array.isArray(incoming)) {
        return res.status(400).json({ success: false, error: 'expenses must be an array' });
    }
    const valid = [], skipped = [];
    incoming.forEach((exp, i) => {
        const errs = validateExpense(exp);
        if (errs.length === 0) {
            valid.push({
                id:       String(exp.id).trim(),
                date:     exp.date,
                amount:   parseFloat(exp.amount),
                currency: exp.currency,
                category: String(exp.category).trim(),
                note:     (exp.note || '').trim()
            });
        } else {
            skipped.push('Row ' + (i + 1) + ': ' + errs.join(', '));
        }
    });
    try {
        let final;
        if (mode === 'merge') {
            const existing    = readAllExpenses();
            const existingIds = new Set(existing.map(e => e.id));
            final = [...existing, ...valid.filter(e => !existingIds.has(e.id))];
        } else {
            final = valid;
        }
        await writeAllExpenses(final);
        res.json({ success: true, saved: final.length, skipped: skipped.length, skippedDetails: skipped });
    } catch (err) {
        console.error('[POST /bulk]', err.message);
        res.status(500).json({ success: false, error: 'Failed to bulk-save expenses' });
    }
});

// POST /api/expenses
expensesRouter.post('/', async (req, res) => {
    const errs = validateExpense(req.body);
    if (errs.length > 0) return res.status(400).json({ success: false, error: errs.join('; ') });
    try {
        const expenses = readAllExpenses();
        if (expenses.some(e => e.id === req.body.id)) {
            return res.status(409).json({ success: false, error: 'Duplicate expense ID' });
        }
        const expense = {
            id:       req.body.id.trim(),
            date:     req.body.date,
            amount:   parseFloat(req.body.amount),
            currency: req.body.currency,
            category: req.body.category.trim(),
            note:     (req.body.note || '').trim()
        };
        expenses.push(expense);
        await writeAllExpenses(expenses);
        res.status(201).json({ success: true, expense });
    } catch (err) {
        console.error('[POST /expenses]', err.message);
        res.status(500).json({ success: false, error: 'Failed to save expense' });
    }
});

// PUT /api/expenses/:id
expensesRouter.put('/:id', async (req, res) => {
    const { id } = req.params;
    if (!id) return res.status(400).json({ success: false, error: 'ID required' });
    const bodyWithId = { ...req.body, id };
    const errs = validateExpense(bodyWithId);
    if (errs.length > 0) return res.status(400).json({ success: false, error: errs.join('; ') });
    try {
        const expenses = readAllExpenses();
        const index    = expenses.findIndex(e => e.id === id);
        if (index === -1) return res.status(404).json({ success: false, error: 'Expense not found' });
        const updated = {
            id,
            date:     req.body.date,
            amount:   parseFloat(req.body.amount),
            currency: req.body.currency,
            category: req.body.category.trim(),
            note:     (req.body.note || '').trim()
        };
        expenses[index] = updated;
        await writeAllExpenses(expenses);
        res.json({ success: true, expense: updated });
    } catch (err) {
        console.error('[PUT /expenses/:id]', err.message);
        res.status(500).json({ success: false, error: 'Failed to update expense' });
    }
});

// DELETE /api/expenses/:id
expensesRouter.delete('/:id', async (req, res) => {
    const { id } = req.params;
    if (!id) return res.status(400).json({ success: false, error: 'ID required' });
    try {
        const expenses = readAllExpenses();
        const next     = expenses.filter(e => e.id !== id);
        if (next.length === expenses.length)
            return res.status(404).json({ success: false, error: 'Expense not found' });
        await writeAllExpenses(next);
        res.json({ success: true, deleted: id });
    } catch (err) {
        console.error('[DELETE /expenses/:id]', err.message);
        res.status(500).json({ success: false, error: 'Failed to delete expense' });
    }
});

// ─── Mount Routes ─────────────────────────────────────────────────────────────
// Mount at /api/expenses
app.use('/api/expenses', expensesRouter);
// Also mount at /expenses for rewrite flexibility
app.use('/expenses', expensesRouter);

// Base API health check
app.get('/api', (req, res) => {
    res.json({ success: true, message: 'ExpenseIQ API is active', timestamp: new Date().toISOString() });
});

app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', uptime: process.uptime() });
});

// Catch-all for undefined /api routes: Always return JSON, NEVER HTML
app.use('/api', (req, res) => {
    res.status(404).json({ success: false, error: `Route not found: ${req.method} ${req.originalUrl}` });
});

// Global Express error handler: Always return JSON, NEVER HTML
app.use((err, req, res, next) => {
    console.error('[API Unhandled Error]', err);
    if (res.headersSent) return next(err);
    res.status(500).json({ success: false, error: err.message || 'Internal server error' });
});

// ─── Local Development Server ──────────────────────────────────────────────────
if (require.main === module) {
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
        const storage = resolveStorage();
        console.log('');
        console.log('  Personal Expense Tracker');
        console.log('  Server   -> http://localhost:' + PORT);
        console.log('  Storage  -> ' + storage.path + (storage.isServerless ? ' [Serverless /tmp]' : ' [Local Disk]'));
        console.log('');
    });
}

module.exports = app;
