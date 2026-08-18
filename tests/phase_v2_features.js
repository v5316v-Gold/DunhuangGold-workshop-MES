const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const OUT = path.join(__dirname, 'v2_screenshots');
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

(async () => {
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
    const page = await ctx.newPage();
    page.on('pageerror', e => console.log('[ERR]', e.message));

    // 1. 工序报工页 - 表格工具条 (搜索 + 排序)
    await page.goto('http://localhost:8080/#workorder_report', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(OUT, '01-table-tools.png') });
    console.log('01-table-tools');

    // 2. 搜表格
    await page.fill('.table-search', 'OWP06');
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, '02-table-search.png') });
    console.log('02-table-search');

    // 3. 清空搜表格 + 收藏 工序报工 + 损耗监控 (回 dashboard 加收藏)
    await page.fill('.table-search', '');
    await page.waitForTimeout(500);
    await page.goto('http://localhost:8080/#dashboard', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    // 收藏 工序报工 + 损耗监控
    await page.click('[data-fav-toggle="workorder_report"]', { force: true });
    await page.waitForTimeout(300);
    await page.click('[data-fav-toggle="loss_monitor"]', { force: true });
    await page.waitForTimeout(300);
    await page.click('[data-fav-toggle="material_batch"]', { force: true });
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, '03-favorites.png') });
    console.log('03-favorites');

    // 4. 折叠"人员"section
    await page.click('[data-section-toggle="人员"]');
    await page.waitForTimeout(500);
    await page.click('[data-section-toggle="安环"]');
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, '04-collapsed.png') });
    console.log('04-collapsed');

    // 5. 面包屑点击
    await page.click('a[data-crumb="dashboard"]');
    await page.waitForTimeout(1500);
    await page.goto('http://localhost:8080/#workorder_report', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(OUT, '05-breadcrumb.png') });
    console.log('05-breadcrumb');

    await browser.close();
})();