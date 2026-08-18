const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const OUT = path.join(__dirname, 'export_screenshots');
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

(async () => {
    const browser = await chromium.launch();
    const ctx = await browser.newContext({
        viewport: { width: 1600, height: 1000 },
        acceptDownloads: true,
    });
    const page = await ctx.newPage();
    page.on('pageerror', e => console.log('[ERR]', e.message));
    page.on('console', m => { if (m.type() === 'error') console.log('[CONSOLE.ERR]', m.text()); });

    // 1. 工序报工 - 表格应有 Excel/PDF 按钮
    await page.goto('http://localhost:8080/#workorder_report', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);  // 等待 CDN 库加载
    await page.screenshot({ path: path.join(OUT, '01-buttons.png') });
    console.log('01 表格有导出按钮');

    // 2. 点击 Excel - 触发下载
    const dl1 = page.waitForEvent('download', { timeout: 10000 });
    await page.click('.export-excel');
    const d1 = await dl1;
    const fn1 = `export-${d1.suggestedFilename()}`;
    await d1.saveAs(path.join(OUT, fn1));
    console.log('02 下载 Excel:', fn1);

    // 3. 点击 PDF
    const dl2 = page.waitForEvent('download', { timeout: 10000 });
    await page.click('.export-pdf');
    const d2 = await dl2;
    const fn2 = `export-${d2.suggestedFilename()}`;
    await d2.saveAs(path.join(OUT, fn2));
    console.log('03 下载 PDF:', fn2);

    // 4. 损耗监控 - 也应可导出
    await page.goto('http://localhost:8080/#loss_monitor', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: path.join(OUT, '04-loss-monitor.png') });
    console.log('04 损耗监控有按钮');

    // 5. 金料批次页
    await page.goto('http://localhost:8080/#material_batch', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: path.join(OUT, '05-material-batch.png') });
    console.log('05 金料批次有按钮');

    // 6. NCR 页
    await page.goto('http://localhost:8080/#ncr', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: path.join(OUT, '06-ncr.png') });
    console.log('06 NCR 有按钮');

    await browser.close();
})();