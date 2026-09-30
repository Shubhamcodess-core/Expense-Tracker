'use strict';

const { Readable } = require('stream');

let _google = null;
function getGoogle() {
    if (!_google) {
        _google = require('googleapis').google;
    }
    return _google;
}

const USERS_CSV_HEADER = 'user_id,name,password_hash,csv_file_id,created_at';
const EXPENSES_CSV_HEADER = 'id,date,amount,currency,category,note';

// ─── CSV Parsing and Escaping Helpers ──────────────────────────────────────────

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

function parseUsersCsv(rawCsv) {
    if (!rawCsv) return [];
    if (rawCsv.charCodeAt(0) === 0xFEFF) rawCsv = rawCsv.slice(1);
    const lines = rawCsv.split(/\r?\n/).filter(l => l.trim() !== '');
    if (lines.length < 2) return [];

    const header = parseCsvLine(lines[0]).map(h => h.trim().toLowerCase());
    const idx = {
        user_id: header.indexOf('user_id'),
        name: header.indexOf('name'),
        password_hash: header.indexOf('password_hash'),
        csv_file_id: header.indexOf('csv_file_id'),
        created_at: header.indexOf('created_at')
    };

    const users = [];
    for (let i = 1; i < lines.length; i++) {
        const cols = parseCsvLine(lines[i]);
        const user_id = idx.user_id >= 0 ? (cols[idx.user_id] || '').trim() : '';
        const name = idx.name >= 0 ? (cols[idx.name] || '').trim() : '';
        const password_hash = idx.password_hash >= 0 ? (cols[idx.password_hash] || '').trim() : '';
        const csv_file_id = idx.csv_file_id >= 0 ? (cols[idx.csv_file_id] || '').trim() : '';
        const created_at = idx.created_at >= 0 ? (cols[idx.created_at] || '').trim() : '';

        if (user_id && name && password_hash && csv_file_id) {
            users.push({ user_id, name, password_hash, csv_file_id, created_at });
        }
    }
    return users;
}

function parseExpensesCsv(rawCsv) {
    if (!rawCsv) return [];
    if (rawCsv.charCodeAt(0) === 0xFEFF) rawCsv = rawCsv.slice(1);
    const lines = rawCsv.split(/\r?\n/).filter(l => l.trim() !== '');
    if (lines.length < 2) return [];

    const header = parseCsvLine(lines[0]).map(h => h.trim().toLowerCase());
    const fields = ['id', 'date', 'amount', 'currency', 'category', 'note'];
    const idx = {};
    fields.forEach(f => { idx[f] = header.indexOf(f); });

    const expenses = [];
    for (let i = 1; i < lines.length; i++) {
        const cols = parseCsvLine(lines[i]);
        const id = idx.id >= 0 ? (cols[idx.id] || '').trim() : '';
        const date = idx.date >= 0 ? (cols[idx.date] || '').trim() : '';
        const amountRaw = idx.amount >= 0 ? (cols[idx.amount] || '').trim() : '';
        const currency = idx.currency >= 0 ? (cols[idx.currency] || '').trim() : 'INR';
        const category = idx.category >= 0 ? (cols[idx.category] || '').trim() : '';
        const note = idx.note >= 0 ? (cols[idx.note] || '').trim() : '';

        const amount = parseFloat(amountRaw);
        if (!id || !date || isNaN(amount) || amount <= 0 || !category) continue;

        expenses.push({ id, date, amount, currency: currency || 'INR', category, note: note || '' });
    }
    return expenses;
}

function serializeExpensesCsv(expenses) {
    const lines = [EXPENSES_CSV_HEADER];
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
    return lines.join('\r\n') + '\r\n';
}

function serializeUsersCsv(users) {
    const lines = [USERS_CSV_HEADER];
    for (const u of users) {
        lines.push([
            csvEscape(u.user_id),
            csvEscape(u.name),
            csvEscape(u.password_hash),
            csvEscape(u.csv_file_id),
            csvEscape(u.created_at || new Date().toISOString())
        ].join(','));
    }
    return lines.join('\r\n') + '\r\n';
}

// ─── Google Drive Client Initialization ─────────────────────────────────────────

const PROD_REDIRECT_URI = 'https://expense-tracker-two-jade-31.vercel.app/api/auth/google/callback';
const DEFAULT_FOLDER_ID = '1iMR64LMXn6Zrl4u4n_DWndai4n-Cws4f';

// In-memory mock store used when MOCK_DRIVE === '1' for automated testing
const mockFiles = new Map();
let mockIdCounter = 1;

function _resetMockDrive() {
    mockFiles.clear();
    mockIdCounter = 1;
    cachedUsersFileId = null;
}

function _getMockFiles() {
    return Array.from(mockFiles.values());
}

function getRedirectUri(req) {
    if (process.env.GOOGLE_REDIRECT_URI) {
        return process.env.GOOGLE_REDIRECT_URI;
    }
    if (req) {
        const host = req.get ? req.get('host') : (req.headers ? req.headers.host : '');
        if (host && (host.includes('localhost') || host.includes('127.0.0.1'))) {
            const proto = req.protocol || 'http';
            return `${proto}://${host}/api/auth/google/callback`;
        }
    }
    return PROD_REDIRECT_URI;
}

function getCredentials() {
    if (process.env.MOCK_DRIVE === '1') {
        return {
            folderId: process.env.GOOGLE_DRIVE_FOLDER_ID || 'mock-folder-id',
            clientId: process.env.GOOGLE_CLIENT_ID || 'mock-client-id',
            clientSecret: process.env.GOOGLE_CLIENT_SECRET || 'mock-client-secret',
            refreshToken: process.env.GOOGLE_REFRESH_TOKEN || 'mock-refresh-token'
        };
    }

    const folderId = process.env.GOOGLE_DRIVE_FOLDER_ID || DEFAULT_FOLDER_ID;
    const clientId = process.env.GOOGLE_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
    const refreshToken = process.env.GOOGLE_REFRESH_TOKEN;

    if (!clientId || !clientSecret || !refreshToken) {
        return null;
    }

    return { folderId, clientId, clientSecret, refreshToken };
}

function getOAuth2Client(redirectUri) {
    const creds = getCredentials();
    const clientId = (creds && creds.clientId) || process.env.GOOGLE_CLIENT_ID || 'mock-client-id';
    const clientSecret = (creds && creds.clientSecret) || process.env.GOOGLE_CLIENT_SECRET || 'mock-client-secret';
    const uri = redirectUri || PROD_REDIRECT_URI;

    const google = getGoogle();
    return new google.auth.OAuth2(clientId, clientSecret, uri);
}

function getDriveClient() {
    if (process.env.MOCK_DRIVE === '1') {
        return { drive: null, folderId: 'mock-folder-id' };
    }

    const creds = getCredentials();
    if (!creds) {
        throw new Error(
            'Google Drive OAuth is not configured. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN in your environment.'
        );
    }

    const google = getGoogle();
    const oauth2Client = new google.auth.OAuth2(
        creds.clientId,
        creds.clientSecret,
        PROD_REDIRECT_URI
    );

    oauth2Client.setCredentials({
        refresh_token: creds.refreshToken
    });

    return {
        drive: google.drive({ version: 'v3', auth: oauth2Client }),
        folderId: creds.folderId
    };
}

// ─── Google Drive File Operations ─────────────────────────────────────────────

async function findFileByName(fileName, folderId) {
    if (process.env.MOCK_DRIVE === '1') {
        for (const file of mockFiles.values()) {
            if (file.name === fileName && file.folderId === folderId) {
                return { id: file.id, name: file.name, mimeType: file.mimeType };
            }
        }
        return null;
    }

    const { drive } = getDriveClient();
    const escapedName = fileName.replace(/'/g, "\\'");
    const res = await drive.files.list({
        q: `'${folderId}' in parents and name = '${escapedName}' and trashed = false`,
        fields: 'files(id, name, mimeType)',
        spaces: 'drive',
        pageSize: 1
    });
    return (res.data.files && res.data.files.length > 0) ? res.data.files[0] : null;
}

async function createCsvFile(fileName, content, folderId) {
    if (process.env.MOCK_DRIVE === '1') {
        const id = `mock_drive_file_${String(mockIdCounter++).padStart(4, '0')}`;
        mockFiles.set(id, {
            id,
            name: fileName,
            content: String(content),
            folderId,
            mimeType: 'text/csv'
        });
        return id;
    }

    const { drive } = getDriveClient();
    const media = {
        mimeType: 'text/csv',
        body: Readable.from([content])
    };
    const res = await drive.files.create({
        requestBody: {
            name: fileName,
            parents: [folderId],
            mimeType: 'text/csv'
        },
        media: media,
        fields: 'id, name'
    });
    return res.data.id;
}

async function readCsvFile(fileId) {
    if (process.env.MOCK_DRIVE === '1') {
        const file = mockFiles.get(fileId);
        if (!file) throw new Error(`Drive file not found: ${fileId}`);
        return file.content;
    }

    const { drive } = getDriveClient();
    const res = await drive.files.get(
        { fileId, alt: 'media' },
        { responseType: 'text' }
    );

    if (res.data && typeof res.data.on === 'function') {
        // Defensive stream handling
        return new Promise((resolve, reject) => {
            let text = '';
            res.data.on('data', chunk => { text += chunk; });
            res.data.on('end', () => resolve(text));
            res.data.on('error', err => reject(err));
        });
    }

    if (typeof res.data === 'string') return res.data;
    if (Buffer.isBuffer(res.data)) return res.data.toString('utf8');
    return JSON.stringify(res.data);
}

async function updateCsvFile(fileId, content) {
    if (process.env.MOCK_DRIVE === '1') {
        const file = mockFiles.get(fileId);
        if (!file) throw new Error(`Drive file not found: ${fileId}`);
        file.content = String(content);
        return fileId;
    }

    const { drive } = getDriveClient();
    const media = {
        mimeType: 'text/csv',
        body: Readable.from([content])
    };
    const res = await drive.files.update({
        fileId,
        media: media,
        fields: 'id, name'
    });
    return res.data.id;
}

// Cached users.csv file ID to minimize list queries
let cachedUsersFileId = null;

async function getOrCreateUsersCsv(folderId) {
    if (cachedUsersFileId) return cachedUsersFileId;
    const existing = await findFileByName('users.csv', folderId);
    if (existing) {
        cachedUsersFileId = existing.id;
        return existing.id;
    }
    const newId = await createCsvFile('users.csv', USERS_CSV_HEADER + '\r\n', folderId);
    cachedUsersFileId = newId;
    return newId;
}

// ─── Exported Service ──────────────────────────────────────────────────────────

module.exports = {
    getCredentials,
    getDriveClient,
    getOAuth2Client,
    getRedirectUri,
    PROD_REDIRECT_URI,
    DEFAULT_FOLDER_ID,
    findFileByName,
    createCsvFile,
    readCsvFile,
    updateCsvFile,
    getOrCreateUsersCsv,
    parseCsvLine,
    csvEscape,
    parseUsersCsv,
    parseExpensesCsv,
    serializeExpensesCsv,
    serializeUsersCsv,
    USERS_CSV_HEADER,
    EXPENSES_CSV_HEADER,
    _resetMockDrive,
    _getMockFiles
};
