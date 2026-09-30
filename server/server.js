'use strict';

// Load .env locally if present
try {
    require('dotenv').config();
} catch (e) {
    // dotenv is optional in environments where variables are pre-injected
}

const express = require('express');
const cookieParser = require('cookie-parser');
const path = require('path');

const drive = require('./drive');
const auth = require('./auth');
const users = require('./users');

const ROOT_DIR = path.join(__dirname, '..');

// Per-user write serialization lock to prevent concurrent Drive CSV corruption
const userLocks = new Map();

function withUserLock(userId, fn) {
    const currentLock = userLocks.get(userId) || Promise.resolve();
    const nextLock = currentLock.then(fn).catch(err => {
        throw err;
    });
    userLocks.set(userId, nextLock);
    return nextLock;
}

// ─── Expense Validation ────────────────────────────────────────────────────────
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

// ─── Express App Initialization ───────────────────────────────────────────────
const app = express();
app.use(express.json());
app.use(cookieParser());

// Serve static frontend when running locally
app.use(express.static(ROOT_DIR, { index: 'index.html' }));

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ─── Authentication Routes (/api/auth) ─────────────────────────────────────────
const authRouter = express.Router();

// GET /api/auth/google — Initiate Google Drive OAuth 2.0 flow
authRouter.get('/google', (req, res) => {
    try {
        const clientId = process.env.GOOGLE_CLIENT_ID;
        const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
        if (!clientId || !clientSecret) {
            return res.status(500).json({
                success: false,
                error: 'GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be configured in environment variables.'
            });
        }

        const redirectUri = drive.getRedirectUri(req);
        const state = auth.createOAuthState({ redirectUri });

        // Set state cookie for anti-CSRF validation
        const isProduction = process.env.NODE_ENV === 'production' || !!process.env.VERCEL;
        res.cookie('oauth_state', state, {
            httpOnly: true,
            secure: isProduction,
            sameSite: 'lax',
            path: '/',
            maxAge: 15 * 60 * 1000
        });

        const oauth2Client = drive.getOAuth2Client(redirectUri);
        const authUrl = oauth2Client.generateAuthUrl({
            access_type: 'offline',
            scope: ['https://www.googleapis.com/auth/drive'],
            include_granted_scopes: true,
            prompt: 'consent',
            state: state
        });

        if (req.headers.accept && req.headers.accept.includes('application/json') && !req.query.redirect) {
            return res.json({ success: true, url: authUrl, state });
        }

        res.redirect(authUrl);
    } catch (err) {
        console.error('[Google OAuth URL Generation Error]', err.message);
        res.status(500).json({ success: false, error: 'Failed to generate authorization URL: ' + err.message });
    }
});

// GET /api/auth/google/callback — Google OAuth 2.0 Callback
authRouter.get('/google/callback', async (req, res) => {
    try {
        const { code, state, error } = req.query;

        if (error) {
            return res.status(400).send(`
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>Authorization Cancelled - ExpenseIQ</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
                        .card { background: #1e293b; border: 1px solid #ef4444; border-radius: 16px; padding: 36px; max-width: 480px; width: 100%; text-align: center; }
                        h2 { color: #f87171; margin-top: 0; }
                        a { color: #38bdf8; text-decoration: none; font-weight: 600; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h2>Google Authorization Cancelled</h2>
                        <p>Google returned an error: <strong>${escapeHtml(error)}</strong></p>
                        <p><a href="/">Return to Expense Tracker</a></p>
                    </div>
                </body>
                </html>
            `);
        }

        if (!code || !state) {
            return res.status(400).json({ success: false, error: 'Missing code or state parameter.' });
        }

        // Validate state
        const stateData = auth.verifyOAuthState(state);
        const cookieState = req.cookies ? req.cookies.oauth_state : null;
        if (!stateData || (cookieState && cookieState !== state)) {
            return res.status(400).json({ success: false, error: 'Invalid or expired OAuth state.' });
        }

        // Clear state cookie
        res.clearCookie('oauth_state', { path: '/' });

        const redirectUri = stateData.redirectUri || drive.getRedirectUri(req);
        const oauth2Client = drive.getOAuth2Client(redirectUri);

        const { tokens } = await oauth2Client.getToken(code);

        // DO NOT log tokens!
        // DO NOT expose refresh token in the response!
        const hasRefreshToken = !!(tokens && tokens.refresh_token);
        console.log('[Google OAuth] Token exchange completed. Refresh token obtained: ' + (hasRefreshToken ? 'YES' : 'NO'));

        if (req.headers.accept && req.headers.accept.includes('application/json')) {
            return res.json({
                success: true,
                message: 'Authorization succeeded. Configure GOOGLE_REFRESH_TOKEN in your environment.',
                hasRefreshToken
            });
        }

        res.send(`
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Google Drive Connected - ExpenseIQ</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }
                    .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 36px; max-width: 520px; width: 100%; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }
                    .icon { width: 56px; height: 56px; border-radius: 12px; background: rgba(34, 197, 94, 0.15); color: #22c55e; display: flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 20px; }
                    h2 { margin: 0 0 12px 0; font-size: 1.5rem; color: #f8fafc; }
                    p { color: #94a3b8; line-height: 1.6; font-size: 0.95rem; margin: 0 0 16px 0; }
                    .notice { background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 16px; margin: 20px 0; color: #93c5fd; font-size: 0.9rem; line-height: 1.5; }
                    .btn { display: inline-block; background: #3b82f6; color: #fff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 0.95rem; margin-top: 8px; transition: background 0.2s; }
                    .btn:hover { background: #2563eb; }
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="icon">✓</div>
                    <h2>Google Drive Authorization Succeeded</h2>
                    <p>The backend has successfully connected to Google OAuth 2.0.</p>
                    <div class="notice">
                        <strong>Configuration Step:</strong><br>
                        Ensure <code>GOOGLE_REFRESH_TOKEN</code> is securely configured in your Vercel Project Environment Variables, along with <code>GOOGLE_CLIENT_ID</code>, <code>GOOGLE_CLIENT_SECRET</code>, and <code>GOOGLE_DRIVE_FOLDER_ID</code>.
                    </div>
                    <a href="/" class="btn">Return to Expense Tracker</a>
                </div>
            </body>
            </html>
        `);
    } catch (err) {
        console.error('[Google OAuth Callback Error]', err.message);
        res.status(500).json({ success: false, error: 'OAuth exchange failed: ' + err.message });
    }
});

// POST /api/auth/register
authRouter.post('/register', async (req, res) => {
    try {
        const { name, password } = req.body || {};
        const registered = await users.registerUser(name, password);

        // Sign and set session cookie
        const token = auth.createSessionToken({
            userId: registered.id,
            name: registered.name
        });
        auth.setSessionCookie(res, token);

        res.status(201).json({
            success: true,
            user: {
                id: registered.id,
                name: registered.name
            }
        });
    } catch (err) {
        const statusCode = err.statusCode || 500;
        res.status(statusCode).json({
            success: false,
            error: err.message || 'Registration failed'
        });
    }
});

// POST /api/auth/login
authRouter.post('/login', async (req, res) => {
    try {
        const { name, password } = req.body || {};
        if (!name || typeof name !== 'string' || !name.trim()) {
            return res.status(400).json({ success: false, error: 'Please enter your name.' });
        }
        if (!password || typeof password !== 'string') {
            return res.status(400).json({ success: false, error: 'Password is required.' });
        }

        const user = await users.findUserByName(name);
        if (!user) {
            return res.status(401).json({ success: false, error: 'Invalid name or password.' });
        }

        const isValid = await auth.verifyPassword(password, user.password_hash);
        if (!isValid) {
            return res.status(401).json({ success: false, error: 'Invalid name or password.' });
        }

        // Sign and set session cookie
        const token = auth.createSessionToken({
            userId: user.user_id,
            name: user.name
        });
        auth.setSessionCookie(res, token);

        res.json({
            success: true,
            user: {
                id: user.user_id,
                name: user.name
            }
        });
    } catch (err) {
        console.error('[Login Error]', err.message);
        res.status(500).json({ success: false, error: err.message || 'Login failed' });
    }
});

// POST /api/auth/logout
authRouter.post('/logout', (req, res) => {
    auth.clearSessionCookie(res);
    res.json({ success: true, message: 'Logged out successfully' });
});

// GET /api/auth/me
authRouter.get('/me', (req, res) => {
    const token = auth.extractToken(req);
    const session = auth.verifySessionToken(token);
    if (!session) {
        return res.status(401).json({ success: false, error: 'Not authenticated' });
    }
    res.json({
        success: true,
        user: {
            id: session.userId,
            name: session.name
        }
    });
});

app.use('/api/auth', authRouter);

// ─── User-Specific Expenses Router (/api/expenses) ────────────────────────────
const expensesRouter = express.Router();

// Require authentication for all expense endpoints
expensesRouter.use(auth.requireAuth);

// GET /api/expenses — Retrieve authenticated user's expenses
expensesRouter.get('/', async (req, res) => {
    try {
        const userId = req.user.userId;
        const csvFileId = await users.getUserCsvFileId(userId);
        const rawCsv = await drive.readCsvFile(csvFileId);
        const userExpenses = drive.parseExpensesCsv(rawCsv);
        res.json({ success: true, expenses: userExpenses });
    } catch (err) {
        console.error('[GET /api/expenses]', err.message);
        res.status(500).json({ success: false, error: 'Failed to read expenses: ' + err.message });
    }
});

// GET /api/expenses/export — Export user's CSV
expensesRouter.get('/export', async (req, res) => {
    try {
        const userId = req.user.userId;
        const csvFileId = await users.getUserCsvFileId(userId);
        const rawCsv = await drive.readCsvFile(csvFileId);
        const safeName = (req.user.name || 'user').replace(/[^a-zA-Z0-9_-]/g, '_');
        res.setHeader('Content-Type', 'text/csv; charset=utf-8');
        res.setHeader('Content-Disposition', `attachment; filename="${safeName}_expenses.csv"`);
        res.send(rawCsv);
    } catch (err) {
        console.error('[GET /api/expenses/export]', err.message);
        res.status(500).json({ success: false, error: 'Failed to export CSV: ' + err.message });
    }
});

// POST /api/expenses/bulk — Bulk replace or merge into user's CSV
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
        const userId = req.user.userId;
        const csvFileId = await users.getUserCsvFileId(userId);

        await withUserLock(userId, async () => {
            const rawCsv = await drive.readCsvFile(csvFileId);
            const existing = drive.parseExpensesCsv(rawCsv);

            let final;
            if (mode === 'merge') {
                const existingIds = new Set(existing.map(e => e.id));
                final = [...existing, ...valid.filter(e => !existingIds.has(e.id))];
            } else {
                final = valid;
            }

            const newContent = drive.serializeExpensesCsv(final);
            await drive.updateCsvFile(csvFileId, newContent);
            res.json({ success: true, saved: final.length, skipped: skipped.length, skippedDetails: skipped });
        });
    } catch (err) {
        console.error('[POST /api/expenses/bulk]', err.message);
        res.status(500).json({ success: false, error: 'Failed to bulk-save expenses: ' + err.message });
    }
});

// POST /api/expenses — Add a single expense to user's CSV
expensesRouter.post('/', async (req, res) => {
    const errs = validateExpense(req.body);
    if (errs.length > 0) {
        return res.status(400).json({ success: false, error: errs.join('; ') });
    }

    try {
        const userId = req.user.userId;
        const csvFileId = await users.getUserCsvFileId(userId);

        await withUserLock(userId, async () => {
            const rawCsv = await drive.readCsvFile(csvFileId);
            const userExpenses = drive.parseExpensesCsv(rawCsv);

            if (userExpenses.some(e => e.id === req.body.id)) {
                return res.status(409).json({ success: false, error: 'Duplicate expense ID' });
            }

            const newExpense = {
                id:       req.body.id.trim(),
                date:     req.body.date,
                amount:   parseFloat(req.body.amount),
                currency: req.body.currency,
                category: req.body.category.trim(),
                note:     (req.body.note || '').trim()
            };

            userExpenses.push(newExpense);
            const updatedCsv = drive.serializeExpensesCsv(userExpenses);
            await drive.updateCsvFile(csvFileId, updatedCsv);

            res.status(201).json({ success: true, expense: newExpense });
        });
    } catch (err) {
        console.error('[POST /api/expenses]', err.message);
        res.status(500).json({ success: false, error: 'Failed to save expense: ' + err.message });
    }
});

// PUT /api/expenses/:id — Update an expense in user's CSV
expensesRouter.put('/:id', async (req, res) => {
    const { id } = req.params;
    if (!id) return res.status(400).json({ success: false, error: 'ID required' });
    const bodyWithId = { ...req.body, id };
    const errs = validateExpense(bodyWithId);
    if (errs.length > 0) return res.status(400).json({ success: false, error: errs.join('; ') });

    try {
        const userId = req.user.userId;
        const csvFileId = await users.getUserCsvFileId(userId);

        await withUserLock(userId, async () => {
            const rawCsv = await drive.readCsvFile(csvFileId);
            const userExpenses = drive.parseExpensesCsv(rawCsv);

            const index = userExpenses.findIndex(e => e.id === id);
            if (index === -1) {
                return res.status(404).json({ success: false, error: 'Expense not found' });
            }

            const updated = {
                id,
                date:     req.body.date,
                amount:   parseFloat(req.body.amount),
                currency: req.body.currency,
                category: req.body.category.trim(),
                note:     (req.body.note || '').trim()
            };

            userExpenses[index] = updated;
            const updatedCsv = drive.serializeExpensesCsv(userExpenses);
            await drive.updateCsvFile(csvFileId, updatedCsv);

            res.json({ success: true, expense: updated });
        });
    } catch (err) {
        console.error('[PUT /api/expenses/:id]', err.message);
        res.status(500).json({ success: false, error: 'Failed to update expense: ' + err.message });
    }
});

// DELETE /api/expenses/:id — Delete an expense from user's CSV
expensesRouter.delete('/:id', async (req, res) => {
    const { id } = req.params;
    if (!id) return res.status(400).json({ success: false, error: 'ID required' });

    try {
        const userId = req.user.userId;
        const csvFileId = await users.getUserCsvFileId(userId);

        await withUserLock(userId, async () => {
            const rawCsv = await drive.readCsvFile(csvFileId);
            const userExpenses = drive.parseExpensesCsv(rawCsv);

            const next = userExpenses.filter(e => e.id !== id);
            if (next.length === userExpenses.length) {
                return res.status(404).json({ success: false, error: 'Expense not found' });
            }

            const updatedCsv = drive.serializeExpensesCsv(next);
            await drive.updateCsvFile(csvFileId, updatedCsv);

            res.json({ success: true, deleted: id });
        });
    } catch (err) {
        console.error('[DELETE /api/expenses/:id]', err.message);
        res.status(500).json({ success: false, error: 'Failed to delete expense: ' + err.message });
    }
});

// Mount expenses router at /api/expenses and /expenses
app.use('/api/expenses', expensesRouter);
app.use('/expenses', expensesRouter);

// ─── Base Health Check ─────────────────────────────────────────────────────────
app.get('/api', (req, res) => {
    res.json({
        success: true,
        message: 'ExpenseIQ Google Drive Backend Active',
        timestamp: new Date().toISOString()
    });
});

app.get('/api/health', (req, res) => {
    const creds = drive.getCredentials();
    res.json({
        status: 'ok',
        storage: creds ? 'google_drive_oauth2' : 'unconfigured',
        uptime: process.uptime()
    });
});

// ─── Catch-all & Error Handlers (Always return JSON) ──────────────────────────
app.use('/api', (req, res) => {
    res.status(404).json({
        success: false,
        error: `Route not found: ${req.method} ${req.originalUrl}`
    });
});

app.use((err, req, res, next) => {
    console.error('[API Unhandled Error]', err.message);
    if (res.headersSent) return next(err);
    res.status(500).json({
        success: false,
        error: err.message || 'Internal server error'
    });
});

// ─── Local Server Start ────────────────────────────────────────────────────────
if (require.main === module) {
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
        const creds = drive.getCredentials();
        console.log('');
        console.log('  ExpenseIQ - Personal Expense Tracker');
        console.log('  Server  -> http://localhost:' + PORT);
        console.log('  Storage -> Google Drive OAuth2 ' + (creds ? '[Configured]' : '[MISSING OAUTH CREDENTIALS in .env]'));
        console.log('');
    });
}

module.exports = app;
