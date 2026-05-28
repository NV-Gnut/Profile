const puppeteer = require('puppeteer-core');
const { CHROME_BIN, BASE_URL, ADMIN_PASSWORD } = require('./config');

async function visitUrl(url) {
  let browser;

  try {
    browser = await puppeteer.launch({
      executablePath: CHROME_BIN,
      headless: 'new',
      args: [
        '--disable-gpu',
        '--disable-popup-blocking',
        '--window-size=1920,1080',
        '--no-sandbox',
        '--disable-dev-shm-usage',
      ],
    });

    const page = await browser.newPage();
    page.setDefaultTimeout(5000);
    page.setDefaultNavigationTimeout(5000);

    await page.goto(`${BASE_URL}/immortal-gate/sign-in`, { waitUntil: 'domcontentloaded' });
    await page.type('input[name="username"]', 'admin');
    await page.type('input[name="password"]', ADMIN_PASSWORD);

    await Promise.allSettled([
      page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 5000 }),
      page.click('#submitBtn'),
    ]);

    await new Promise((resolve) => setTimeout(resolve, 1000));
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 5000 });
    await new Promise((resolve) => setTimeout(resolve, 1000));
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

module.exports = {
  visitUrl,
};
