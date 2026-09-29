'use strict';

const drive = require('./drive');
const auth = require('./auth');

// In-memory cache for user metadata to minimize Drive round-trips
let usersCache = null;
let usersCacheTime = 0;
const CACHE_TTL_MS = 60 * 1000; // 1 minute

async function loadUsers(forceRefresh = false) {
    const now = Date.now();
    if (!forceRefresh && usersCache !== null && (now - usersCacheTime) < CACHE_TTL_MS) {
        return usersCache;
    }

    const { folderId } = drive.getDriveClient();
    const usersFileId = await drive.getOrCreateUsersCsv(folderId);
    const rawCsv = await drive.readCsvFile(usersFileId);
    const users = drive.parseUsersCsv(rawCsv);

    usersCache = users;
    usersCacheTime = now;
    return users;
}

async function findUserByName(name) {
    if (!name || typeof name !== 'string') return null;
    const clean = name.trim().toLowerCase();
    const users = await loadUsers();
    return users.find(u => u.name.trim().toLowerCase() === clean) || null;
}

async function findUserById(userId) {
    if (!userId || typeof userId !== 'string') return null;
    const users = await loadUsers();
    return users.find(u => u.user_id === userId) || null;
}

async function getUserCsvFileId(userId) {
    let user = await findUserById(userId);
    // If not found in cache, force fresh read from Drive in case user was just created
    if (!user) {
        user = (await loadUsers(true)).find(u => u.user_id === userId);
    }
    if (!user) {
        throw new Error('User record not found');
    }
    return user.csv_file_id;
}

async function registerUser(name, password) {
    if (!name || typeof name !== 'string' || name.trim() === '') {
        const err = new Error('Please enter your name.');
        err.statusCode = 400;
        throw err;
    }

    if (!password || typeof password !== 'string' || password.length < 6) {
        const err = new Error('Password must contain at least 6 characters.');
        err.statusCode = 400;
        throw err;
    }

    const trimmedName = name.trim();

    // Check duplicate name case-insensitively (always load fresh from Drive)
    const currentUsers = await loadUsers(true);
    const exists = currentUsers.some(
        u => u.name.trim().toLowerCase() === trimmedName.toLowerCase()
    );
    if (exists) {
        const err = new Error('A user with this name already exists.');
        err.statusCode = 409;
        throw err;
    }

    // Determine next sequential user ID: user_001, user_002, ...
    let maxNum = 0;
    for (const u of currentUsers) {
        const match = u.user_id.match(/^user_(\d+)$/);
        if (match) {
            const num = parseInt(match[1], 10);
            if (!isNaN(num) && num > maxNum) maxNum = num;
        }
    }
    const nextNum = maxNum + 1;
    const userId = `user_${String(nextNum).padStart(3, '0')}`;

    const { folderId } = drive.getDriveClient();

    // 1. Create personal CSV in Google Drive: user_XXX.csv
    const userCsvName = `${userId}.csv`;
    const initialCsvContent = drive.EXPENSES_CSV_HEADER + '\r\n';
    const csvFileId = await drive.createCsvFile(userCsvName, initialCsvContent, folderId);

    // 2. Hash password securely using scrypt
    const passwordHash = await auth.hashPassword(password);

    // 3. Append user record to users.csv in Google Drive
    const newUser = {
        user_id: userId,
        name: trimmedName,
        password_hash: passwordHash,
        csv_file_id: csvFileId,
        created_at: new Date().toISOString()
    };

    const usersFileId = await drive.getOrCreateUsersCsv(folderId);
    const updatedUsers = [...currentUsers, newUser];
    const updatedUsersCsv = drive.serializeUsersCsv(updatedUsers);
    await drive.updateCsvFile(usersFileId, updatedUsersCsv);

    // Update cache
    usersCache = updatedUsers;
    usersCacheTime = Date.now();

    return {
        id: userId,
        name: trimmedName,
        csv_file_id: csvFileId
    };
}

module.exports = {
    loadUsers,
    findUserByName,
    findUserById,
    getUserCsvFileId,
    registerUser
};
