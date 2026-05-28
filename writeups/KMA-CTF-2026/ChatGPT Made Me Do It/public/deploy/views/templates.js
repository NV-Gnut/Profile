const STYLES_LINK = '<link rel="stylesheet" href="/styles.css">';

const BASE_HTML = (title, content) => `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${title}</title>
  ${STYLES_LINK}
</head>
<body>
  ${content}
</body>
</html>
`;

const renderHomepage = (username) => {
  const safeUsername = decodeURIComponent(String(username || 'guest'));
  const navAdmin = safeUsername === 'admin' ? `
    <a href="/immortal-gate/treasure">🏆 Tông môn bí tịch</a><br><br>
  ` : '';

  const navUser = safeUsername !== 'guest' ? `
    <a href="/cultivation/password">⚔️ Tu sửa công pháp</a><br><br>
    <a href="/immortal-gate/report">📜 Thượng báo ngộ pháp</a><br><br>
  ` : '';

  const content = `
    <div class="container">
      <h1>Hoàng Phong Cốc</h1>
      <div class="welcome">
        Kiếm khách <span style="color: #00FFFF;">${safeUsername}</span> hoan nghênh quay về tông môn!
      </div>
      <div class="nav-links">
        <a href="/">🏠 Tông môn đại sảnh</a><br><br>
        ${navUser}
        ${navAdmin}
        <a href="/immortal-gate/sign-in">🔐 Tiến nhập tông môn</a><br><br>
        <a href="/immortal-gate/sign-up">✨ Gia nhập tông môn</a>
      </div>
    </div>
  `;

  return BASE_HTML('⚔️ Hoàng Phong Cốc ⚔️', content);
};

const renderLogin = () => {
  const content = `
    <div class="container">
      <div class="title-cn">🌟 Tiến nhập tông môn 🌟</div>
      <h1>Đăng nhập tu hành</h1>
      <form method="post">
        <div class="form-group">
          <label>⚔️ Kiếm khách chi danh：</label>
          <input type="text" name="username" required>
        </div>
        <div class="form-group">
          <label>🔐 Tâm pháp bí điển：</label>
          <input type="password" name="password" required>
        </div>
        <input type="submit" id="submitBtn" value="☄️ Tiến nhập tu hành ☄️">
      </form>
      <div class="nav-links">
        <a href="/immortal-gate/sign-up">✨ Gia nhập tân thủ</a>
        <a href="/">🏠 Quay về</a>
      </div>
    </div>
  `;

  return BASE_HTML('⚔️ Tiến nhập tông môn ⚔️', content);
};

const renderRegister = () => {
  const content = `
    <div class="container">
      <div class="title-cn">🌠 Tân thủ nhập môn 🌠</div>
      <h1>Gia nhập tông môn</h1>
      <form method="post">
        <div class="form-group">
          <label>⚔️ Thủ một đạo hiệu：</label>
          <input type="text" name="username" required>
        </div>
        <div class="form-group">
          <label>🔐 Thiết lập tâm pháp：</label>
          <input type="password" name="password" required>
        </div>
        <input type="submit" value="✨ Bái nhập tông môn ✨">
      </form>
      <div class="nav-links">
        <a href="/immortal-gate/sign-in">🔐 Đã nhập môn</a>
        <a href="/">🏠 Quay về</a>
      </div>
    </div>
  `;

  return BASE_HTML('✨ Gia nhập tông môn ✨', content);
};

const renderChangePassword = (csrfToken, username) => {
  const safeUsername = decodeURIComponent(String(username || ''));
  const content = `
    <div class="container">
      <div class="title-cn">🔥 Tu hành đột phá 🔥</div>
      <h1>Tu sửa công pháp</h1>
      <div class="welcome">Kiếm khách ${safeUsername} tu hành chi lộ</div>
      <form method="post">
        <div class="form-group">
          <label>🌟 Tân chi tâm pháp bí điển：</label>
          <input type="password" name="new_password" required>
        </div>
        <input type="submit" value="⚡ Khai ngộ đột phá ⚡">
      </form>
      <div class="nav-links">
        <a href="/">🏠 Quay về tông môn</a>
      </div>
    </div>
  `;

  return BASE_HTML('⚔️ Tu sửa công pháp ⚔️', content);
};

const renderReport = (csrfToken) => {
  const content = `
    <div class="container">
      <div class="title-cn">🔔 Cử báo dị đoan 🔔</div>
      <h1>Thượng báo ngộ pháp</h1>
      <div class="welcome">Phát hiện khả nghi liên kết? Vui lòng thượng báo cho chưởng môn!</div>
      <form method="post">
        <div class="form-group">
          <label>🌐 Ngộ pháp liên kết：</label>
          <input type="text" name="url" placeholder="https://..." required>
        </div>
        <input type="submit" value="⚡ Thượng báo cử báo ⚡">
      </form>
      <div class="nav-links">
        <a href="/">🏠 Quay về tông môn</a>
      </div>
    </div>
  `;

  return BASE_HTML('📜 Thượng báo ngộ pháp 📜', content);
};

const renderFlag = (flag) => {
  const safeFlag = decodeURIComponent(String(flag || ''));
  const content = `
    <div class="container">
      <div class="title-cn">🌟 Chí bảo bí tịch 🌟</div>
      <h1>Tông môn bí tịch</h1>
      <div class="welcome" style="word-break: break-all; font-size: 8px;">
        ${safeFlag}
      </div>
      <div class="nav-links">
        <a href="/">🏠 Quay về tông môn</a>
      </div>
    </div>
  `;

  return BASE_HTML('🏆 Tông môn bí tịch 🏆', content);
};

module.exports = {
  renderHomepage,
  renderLogin,
  renderRegister,
  renderChangePassword,
  renderReport,
  renderFlag,
};
