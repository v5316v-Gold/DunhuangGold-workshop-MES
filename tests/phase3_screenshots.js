const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'phase3_screenshots');
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

(async () => {
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();

    const pages = [
        ['dashboard', '车间看板'],
        ['bigscreen', '车间大屏'],
        ['production_list', '任务单接收'],
        ['flow_card', '工序交接卡'],
        ['piece_trace', '件级追溯'],
        ['ncr', 'NCR 不合格品'],
        ['package', '包装'],
    ];

    for (const [pageId, name] of pages) {
        try {
            await page.goto(`http://localhost:8080/#${pageId}`, { waitUntil: 'networkidle' });
            await page.waitForTimeout(1500);
            const file = path.join(OUT, `${pageId}.png`);
            await page.screenshot({ path: file, fullPage: false });
            console.log(`[OK] ${pageId} (${name}) → ${file}`);
        } catch (e) {
            console.log(`[FAIL] ${pageId}: ${e.message}`);
        }
    }
    await browser.close();
})();