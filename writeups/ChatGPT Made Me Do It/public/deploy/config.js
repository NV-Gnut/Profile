const crypto = require('crypto');

const PORT = Number(process.env.PORT || 3000);
const FLAG = process.env.FLAG || 'KMACTF{FAKE_FLAG}';
const ADMIN_PASSWORD = crypto.randomBytes(16).toString('hex');
const SESSION_SECRET = crypto.randomBytes(32).toString('hex');
const BASE_URL = process.env.BASE_URL || `http://localhost:${PORT}`;
const CHROME_BIN = process.env.CHROME_BIN || '/usr/bin/chromium';

const users = new Map([
  ['admin', ADMIN_PASSWORD],
]);

module.exports = {
  PORT,
  FLAG,
  ADMIN_PASSWORD,
  SESSION_SECRET,
  BASE_URL,
  CHROME_BIN,
  users,
};
