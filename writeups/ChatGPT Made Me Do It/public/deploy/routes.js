const express = require('express');
const crypto = require('crypto');
const { users, FLAG } = require('./config');
const { alertBack } = require('./utils');
const { visitUrl } = require('./bot');
const {
  renderHomepage,
  renderLogin,
  renderRegister,
  renderChangePassword,
  renderReport,
  renderFlag,
} = require('./views/templates');
const e = require('express');

const router = express.Router();

function santi(str) {
  const tag = str.match(/<([^>]*)>/);

  if (tag && /[a-zA-Z]/.test(tag[1])) {
    return 'no hack';
  }

  return str;
}

router.all('/', (req, res) => {
  res.send(renderHomepage(req.session.username));
});

router.all('/immortal-gate/sign-in', (req, res) => {
  if (req.method === 'GET') return res.send(renderLogin());

  const username = req.body.username;
  const password = req.body.password;

  if (users.get(username) === password) {
    res.cookie('csrf_token', crypto.randomBytes(16).toString('hex'), {
      httpOnly: true,
      path: '/',
      sameSite: 'strict',
    });
    req.session.username = username;
    return res.redirect('/');
  }

  return res.send(alertBack('❌ Tâm pháp sai lạc, xin thử lại!'));
});

router.all('/immortal-gate/sign-up', (req, res) => {
  if (req.method === 'GET') return res.send(renderRegister());

  const username = req.body.username;
  const password = req.body.password;

  if (users.has(username)) {
    return res.send(`<script>alert('❌ Đạo hiệu này đã bị chiếm dụng, xin chọn khác!');history.go(-1);</script>`);
  }

  users.set(username, password);
  return res.redirect('/immortal-gate/sign-in');
});

router.all('/cultivation/password', (req, res) => {
  const username = req.session?.username;
  const csrfToken = req.cookies.csrf_token;

  if (username === undefined) {
    return res.redirect('/immortal-gate/sign-in');
  } 

  if (req.headers['x-csrf-token'] !== csrfToken) {
    return res.send(alertBack('❌ Tâm ma tác sai, công kích bị ngăn chặn!'));
  }

  const newPassword = req.body.new_password || '';
  users.set(username, newPassword);

  return res.send(alertBack('✨ Công pháp tu sửa thành công!'));
});

router.all('/immortal-gate/treasure', (req, res) => {
  if (req.method !== 'POST') return res.redirect('/');

  const username = req.session.username;

  if (username !== 'admin') {
    return res.redirect('/');
  }

  return res.send(renderFlag(FLAG));
});

router.all('/immortal-gate/report', (req, res) => {
  const username = req.session.username;

  if (username === undefined) return res.redirect('/immortal-gate/sign-in');

  if (req.method === 'GET') return res.send(renderReport());

  const url = req.body.url || '';
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return res.send(alertBack('❌ Liên kết định dạng sai, phải bắt đầu bằng http:// hoặc https://!'));
  }

  visitUrl(url).catch((error) => {
    console.error(`Error occurred: ${error && error.stack ? error.stack : error}`);
  });

  return res.send(alertBack('✨ Đã thượng báo cho chưởng môn, cảm ơn cử báo!'));
});

router.all('/immortal-gate/check', (req, res) => {
  const name = req.query.name || req.session.username || '';
  res.write(`${santi(decodeURIComponent(String(name)))}, hello`);
  res.end();
});

module.exports = router;