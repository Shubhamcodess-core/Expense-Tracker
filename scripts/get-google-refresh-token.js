/**
 * LOCAL-ONLY GOOGLE OAUTH REFRESH TOKEN SETUP UTILITY
 * 
 * This script is strictly for one-time local OAuth setup and MUST NOT be deployed
 * as a Vercel API route.
 * 
 * It starts a temporary local HTTP server on port 3000, generates a Google OAuth
 * consent URL for your personal Google Drive, captures the callback, exchanges
 * the authorization code, prints ONLY the GOOGLE_REFRESH_TOKEN to your local
 * terminal, and exits immediately.
 * 
 * Prerequisites:
 * - GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env or environment variables.
 * - Authorized redirect URI in Google Cloud Console:
 *   http://localhost:3000/api/auth/google/callback
 */

'use strict';

const http = require('http');
const path = require('path');
const { exec } = require('child_process');

// Load environment variables from .env if present
try {
    require('dotenv').config({ path: path.join(__dirname, '..', '.env') });
} catch (e) {
    // dotenv is optional if variables are already set in environment
}

let _google = null;
function getGoogle() {
    if (!_google) {
        _google = require('googleapis').google;
    }
    return _google;
}

const PORT = 3000;
const REDIRECT_URI = `http://localhost:${PORT}/api/auth/google/callback`;

async function main() {
    const clientId = process.env.GOOGLE_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET;

    if (!clientId || !clientSecret || clientId.trim() === '' || clientSecret.trim() === '') {
        console.error('');
        console.error('❌ ERROR: Missing Google OAuth Client credentials.');
        console.error('');
        console.error('Please make sure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are defined');
        console.error('in your .env file or passed in your environment:');
        console.error('');
        console.error('  GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com');
        console.error('  GOOGLE_CLIENT_SECRET=GOCSPX-your_client_secret');
        console.error('');
        process.exit(1);
    }

    const google = getGoogle();
    const oauth2Client = new google.auth.OAuth2(
        clientId.trim(),
        clientSecret.trim(),
        REDIRECT_URI
    );

    // Generate consent URL requesting offline access to Google Drive
    const authUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: ['https://www.googleapis.com/auth/drive'],
        prompt: 'consent',
        include_granted_scopes: true
    });

    let server;

    server = http.createServer(async (req, res) => {
        try {
            const reqUrl = new URL(req.url, `http://localhost:${PORT}`);

            if (reqUrl.pathname === '/api/auth/google/callback') {
                const code = reqUrl.searchParams.get('code');
                const error = reqUrl.searchParams.get('error');

                if (error) {
                    res.writeHead(400, { 'Content-Type': 'text/html; charset=utf-8' });
                    res.end(`
                        <!DOCTYPE html>
                        <html>
                        <head><title>Authorization Failed</title><style>body{font-family:sans-serif;background:#0f172a;color:#f8fafc;display:flex;align-items:center;justify-content:center;height:90vh;} .card{background:#1e293b;border:1px solid #ef4444;padding:32px;border-radius:12px;text-align:center;max-width:480px;} h2{color:#f87171;margin-top:0;}</style></head>
                        <body>
                            <div class="card">
                                <h2>Google Authorization Cancelled</h2>
                                <p>Error from Google: <strong>${error}</strong></p>
                                <p>Check your terminal for details.</p>
                            </div>
                        </body>
                        </html>
                    `);

                    console.error('');
                    console.error(`❌ Google returned an authorization error: ${error}`);
                    console.error('');
                    server.close(() => process.exit(1));
                    return;
                }

                if (!code) {
                    res.writeHead(400, { 'Content-Type': 'text/html; charset=utf-8' });
                    res.end('<h3>Missing authorization code from Google callback.</h3>');
                    return;
                }

                // Exchange code for tokens (NEVER print or expose access token or code!)
                const { tokens } = await oauth2Client.getToken(code);

                if (!tokens || !tokens.refresh_token) {
                    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
                    res.end(`
                        <!DOCTYPE html>
                        <html>
                        <head><title>No Refresh Token</title><style>body{font-family:sans-serif;background:#0f172a;color:#f8fafc;display:flex;align-items:center;justify-content:center;height:90vh;} .card{background:#1e293b;border:1px solid #f59e0b;padding:32px;border-radius:12px;text-align:center;max-width:500px;} h2{color:#fbbf24;margin-top:0;}</style></head>
                        <body>
                            <div class="card">
                                <h2>No Refresh Token Received</h2>
                                <p>Google authorized the request but did not return a new refresh token.</p>
                                <p>This occurs if consent was already granted earlier. Revoke app access in your Google Account security settings and re-run this script.</p>
                            </div>
                        </body>
                        </html>
                    `);

                    console.warn('');
                    console.warn('⚠️ WARNING: Google did not return a refresh token.');
                    console.warn('This typically happens if consent was previously granted.');
                    console.warn('Go to https://myaccount.google.com/permissions, remove access for this app, and run this script again.');
                    console.warn('');
                    server.close(() => process.exit(1));
                    return;
                }

                // Success response to browser — NEVER expose the refresh token in the browser!
                res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
                res.end(`
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>Authorization Successful - ExpenseIQ</title>
                        <style>
                            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 90vh; margin: 0; }
                            .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 40px; max-width: 500px; text-align: center; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }
                            .icon { width: 56px; height: 56px; border-radius: 12px; background: rgba(34, 197, 94, 0.15); color: #22c55e; display: inline-flex; align-items: center; justify-content: center; font-size: 28px; margin-bottom: 20px; }
                            h2 { margin: 0 0 12px 0; color: #f8fafc; }
                            p { color: #94a3b8; line-height: 1.6; font-size: 0.95rem; margin: 0 0 16px 0; }
                            .badge { display: inline-block; background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 6px; padding: 8px 16px; font-size: 0.9rem; font-weight: 500; }
                        </style>
                    </head>
                    <body>
                        <div class="card">
                            <div class="icon">✓</div>
                            <h2>Authorization Successful!</h2>
                            <p>You can close this browser tab.</p>
                            <div class="badge">Return to your terminal to copy your GOOGLE_REFRESH_TOKEN.</div>
                        </div>
                    </body>
                    </html>
                `);

                // Print ONLY the refresh token to the local terminal, clearly labeled
                console.log('');
                console.log('==================================================================');
                console.log('🎉 GOOGLE DRIVE OAUTH 2.0 REFRESH TOKEN OBTAINED SUCCESSFULLY');
                console.log('==================================================================');
                console.log('');
                console.log('Copy and add this line to your .env file and Vercel Environment Variables:');
                console.log('');
                console.log(`GOOGLE_REFRESH_TOKEN=${tokens.refresh_token}`);
                console.log('');
                console.log('==================================================================');
                console.log('The temporary setup server will now shut down.');
                console.log('');

                server.close(() => {
                    process.exit(0);
                });
                return;
            }

            // Redirect any other route to the authorization URL
            res.writeHead(302, { 'Location': authUrl });
            res.end();
        } catch (err) {
            console.error('❌ Error handling callback:', err.message);
            res.writeHead(500, { 'Content-Type': 'text/plain' });
            res.end('Internal Server Error during OAuth exchange.');
            server.close(() => process.exit(1));
        }
    });

    server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') {
            console.error('');
            console.error(`❌ Port ${PORT} is currently in use.`);
            console.error('Please stop any existing server (e.g., run stop.bat or terminate existing node processes), then try again.');
            console.error('');
        } else {
            console.error('❌ Server error:', err.message);
        }
        process.exit(1);
    });

    server.listen(PORT, () => {
        console.log('');
        console.log('==================================================================');
        console.log('  Google OAuth Refresh Token Setup Utility (Local-Only)');
        console.log('==================================================================');
        console.log('');
        console.log(`- Listening for callback on: ${REDIRECT_URI}`);
        console.log('');
        console.log('Opening your browser to complete Google authorization...');
        console.log('If the browser does not open automatically, copy and paste this URL:');
        console.log('');
        console.log(authUrl);
        console.log('');
        console.log('Waiting for authorization from Google...');

        // Attempt to launch browser automatically
        const openCmd = process.platform === 'win32' ? `start "" "${authUrl}"`
                      : process.platform === 'darwin' ? `open "${authUrl}"`
                      : `xdg-open "${authUrl}"`;

        exec(openCmd, (err) => {
            if (err) {
                // Ignore launch error; the user can open the printed URL manually
            }
        });
    });
}

main().catch((err) => {
    console.error('❌ Fatal error:', err.message);
    process.exit(1);
});
