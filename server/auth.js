'use strict';

const crypto = require('crypto');

const COOKIE_NAME = 'expenseiq_session';
const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

function getSessionSecret() {
    const secret = process.env.SESSION_SECRET;
    if (!secret || secret.trim() === '') {
        // Fallback for local testing if not yet configured, but warn
        return 'expenseiq-secure-dev-session-secret-change-in-prod';
    }
    return secret;
}

// ─── Scrypt Password Hashing ──────────────────────────────────────────────────

function hashPassword(password) {
    return new Promise((resolve, reject) => {
        const salt = crypto.randomBytes(16).toString('hex');
        crypto.scrypt(password, salt, 64, (err, derivedKey) => {
            if (err) return reject(err);
            resolve(`${salt}:${derivedKey.toString('hex')}`);
        });
    });
}

function verifyPassword(password, storedHash) {
    return new Promise((resolve) => {
        if (!storedHash || typeof storedHash !== 'string') return resolve(false);
        const parts = storedHash.split(':');
        if (parts.length !== 2) return resolve(false);
        const [salt, expectedKeyHex] = parts;
        crypto.scrypt(password, salt, 64, (err, derivedKey) => {
            if (err) return resolve(false);
            try {
                const expectedBuffer = Buffer.from(expectedKeyHex, 'hex');
                if (derivedKey.length !== expectedBuffer.length) return resolve(false);
                const match = crypto.timingSafeEqual(derivedKey, expectedBuffer);
                resolve(match);
            } catch {
                resolve(false);
            }
        });
    });
}

// ─── Signed Session Tokens (HMAC-SHA256) ───────────────────────────────────────

function base64UrlEncode(str) {
    return Buffer.from(str, 'utf8').toString('base64url');
}

function base64UrlDecode(str) {
    return Buffer.from(str, 'base64url').toString('utf8');
}

function createSessionToken(payload) {
    const secret = getSessionSecret();
    const data = {
        userId: payload.userId,
        name: payload.name,
        exp: Date.now() + SESSION_TTL_MS
    };
    const payloadB64 = base64UrlEncode(JSON.stringify(data));
    const signature = crypto
        .createHmac('sha256', secret)
        .update(payloadB64)
        .digest('base64url');
    return `${payloadB64}.${signature}`;
}

function verifySessionToken(token) {
    if (!token || typeof token !== 'string') return null;
    const parts = token.split('.');
    if (parts.length !== 2) return null;
    const [payloadB64, signature] = parts;
    const secret = getSessionSecret();
    const expectedSig = crypto
        .createHmac('sha256', secret)
        .update(payloadB64)
        .digest('base64url');

    try {
        const sigA = Buffer.from(signature);
        const sigB = Buffer.from(expectedSig);
        if (sigA.length !== sigB.length || !crypto.timingSafeEqual(sigA, sigB)) {
            return null;
        }
        const data = JSON.parse(base64UrlDecode(payloadB64));
        if (!data || !data.userId || !data.exp || data.exp < Date.now()) {
            return null;
        }
        return {
            userId: data.userId,
            name: data.name
        };
    } catch {
        return null;
    }
}

// ─── Cookie Helpers ────────────────────────────────────────────────────────────

function setSessionCookie(res, token) {
    const isProduction = process.env.NODE_ENV === 'production' || !!process.env.VERCEL;
    res.cookie(COOKIE_NAME, token, {
        httpOnly: true,
        secure: isProduction,
        sameSite: 'lax',
        path: '/',
        maxAge: SESSION_TTL_MS
    });
}

function clearSessionCookie(res) {
    const isProduction = process.env.NODE_ENV === 'production' || !!process.env.VERCEL;
    res.clearCookie(COOKIE_NAME, {
        httpOnly: true,
        secure: isProduction,
        sameSite: 'lax',
        path: '/'
    });
}

function extractToken(req) {
    if (req.cookies && req.cookies[COOKIE_NAME]) {
        return req.cookies[COOKIE_NAME];
    }
    // Fallback: manually parse Cookie header if cookieParser was bypassed
    const cookieHeader = req.headers.cookie;
    if (cookieHeader) {
        const cookies = cookieHeader.split(';').map(c => c.trim());
        for (const c of cookies) {
            if (c.startsWith(`${COOKIE_NAME}=`)) {
                return decodeURIComponent(c.slice(COOKIE_NAME.length + 1));
            }
        }
    }
    return null;
}

// ─── Express Middleware ────────────────────────────────────────────────────────

function requireAuth(req, res, next) {
    const token = extractToken(req);
    const session = verifySessionToken(token);
    if (!session) {
        return res.status(401).json({
            success: false,
            error: 'Authentication required'
        });
    }
    req.user = session;
    next();
}

module.exports = {
    COOKIE_NAME,
    hashPassword,
    verifyPassword,
    createSessionToken,
    verifySessionToken,
    setSessionCookie,
    clearSessionCookie,
    extractToken,
    requireAuth
};
