const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const OUT = path.join(__dirname, 'menu_screenshots');
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

(async () => {
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
    const page = await ctx.newPage();
    page.on('pageerror', e => console.log('[ERR]', e.message));

    // 1. 初始状态: 大菜单 + 9 sections
    await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(OUT, '01-default.png') });
    console.log('01-default');

    // 2. 访问几个页面后: 最近访问应出现
    await page.goto('http://localhost:8080/#dashboard', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.goto('http://localhost:8080/#loss_monitor', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.goto('http://localhost:8080/#piece_trace', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(OUT, '02-with-recent.png') });
    console.log('02-with-recent');

    // 3. 搜索 "金料" - 应过滤
    await page.fill('.navbar .search', '金料');
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, '03-search-jinliao.png') });
    console.log('03-search-jinliao');

    // 4. 搜索 "损耗" - 应匹配多个
    await page.fill('.navbar .search', '损耗');
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, '04-search-sunhao.png') });
    console.log('04-search-sunhao');

    // 5. 搜索 "NCR"
    await page.fill('.navbar .search', 'NCR');
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, '05-search-ncr.png') });
    console.log('05-search-ncr');

    // 6. 搜索无结果
    await page.fill('.navbar .search', 'xyz不存在的关键词');
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, '06-search-empty.png') });
    console.log('06-search-empty');

    // 7. 清空搜索,访问 工序报工 看 active 状态
    await page.fill('.navbar .search', '');
    await page.waitForTimeout(500);
    await page.goto('http://localhost:8080/#workorder_report', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(OUT, '07-active-state.png') });
    console.log('07-active-state');

    // 8. PDA 视口
    await page.setViewportSize({ width: 414, height: 800 });
    await page.goto('http://localhost:8080/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(OUT, '08-pda.png') });
    console.log('08-pda');

    await browser.close();
})();