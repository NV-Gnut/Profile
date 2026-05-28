function alertBack(message) {
  return `<!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>⚠️ Hệ thống thông báo ⚠️</title>
      <link rel="stylesheet" href="/styles.css">
    </head>
    <body class="alert-page">
      <div class="alert-box">
        <div class="alert-title">⚡ Hệ thống thông báo ⚡</div>
        <div class="alert-message">${message}</div>
        <button class="alert-button" onclick="history.go(-1)">← Quay về</button>
      </div>
    </body>
    </html>`;
}

module.exports = {
  alertBack,
};
