#!/usr/bin/env node
/**
 * Playwright UI 巡检 — 截图每个页面,检查布局问题
 * 运行: node tests/ui_inspect.js
 * 依赖: playwright (npm install playwright + npx playwright install chromium)
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const URL = 'http://localhost:8080';
const OUT_DIR = path.join(__dirname, 'ui_screenshots');
const VIEWPORTS = [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'tablet',  width: 1024, height: 768 },
    { name: 'pda',     width: 414,  height: 800 },
];

const PAGES = [
    'dashboard',
    'material_batch',
    'workorder_report',
    'environment',
    'hazardous_chemical',
    'inventory_count',
    'finished_goods',
    'maintenance',
];

(async () => {
    if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
    const browser = await chromium.launch();
    const issues = [];

    for (const vp of VIEWPORTS) {
        console.log(`\n=== Viewport: ${vp.name} (${vp.width}x${vp.height}) ===`);
        const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
        const page = await context.newPage();

        // 收集 console 错误
        page.on('console', msg => {
            if (msg.type() === 'error') {
                issues.push({ viewport: vp.name, type: 'console.error', text: msg.text() });
                console.log(`  [CONSOLE.ERROR] ${msg.text()}`);
            }
        });
        page.on('pageerror', err => {
            issues.push({ viewport: vp.name, type: 'pageerror', text: err.message });
            console.log(`  [PAGE.ERROR] ${err.message}`);
        });

        for (const pageId of PAGES) {
            try {
                await page.goto(`${URL}/#${pageId}`, { waitUntil: 'networkidle', timeout: 8000 });
                // 等渲染完成
                await page.waitForTimeout(800);
                const file = path.join(OUT_DIR, `${vp.name}_${pageId}.png`);
                await page.screenshot({ path: file, fullPage: false });
                console.log(`  ✓ ${pageId} → ${file}`);

                // 检查布局问题
                const check = await page.evaluate((pid) => {
                    const out = { pid };
                    const main = document.querySelector('.main');
                    if (!main) { out.error = 'no .main'; return out; }
                    const mainBox = main.getBoundingClientRect();
                    out.mainRect = { w: mainBox.width, h: mainBox.height };
                    // 检查内容是否被遮挡
                    const bodyRect = document.body.getBoundingClientRect();
                    out.bodyOverflow = mainBox.right > bodyRect.right ? 'right-overflow' : 'ok';

                    // KPI 卡
                    const kpis = document.querySelectorAll('.kpi-card');
                    if (kpis.length) {
                        out.kpiCount = kpis.length;
                        const first = kpis[0].getBoundingClientRect();
                        out.firstKpi = { w: first.width, h: first.height };
                    }
                    // 表格
                    const table = document.querySelector('table');
                    if (table) {
                        const tBox = table.getBoundingClientRect();
                        out.tableRect = { w: tBox.width, h: tBox.height };
                    }
                    // 空状态
                    const empty = document.querySelector('.empty-state');
                    out.hasEmptyState = !!empty;
                    return out;
                }, pageId);
                console.log(`     ${JSON.stringify(check)}`);
            } catch (e) {
                issues.push({ viewport: vp.name, page: pageId, type: 'nav-error', text: e.message });
                console.log(`  ✗ ${pageId}: ${e.message}`);
            }
        }
        await context.close();
    }

    await browser.close();

    console.log('\n============================================================');
    console.log(`巡检完成: ${issues.length} 个问题`);
    console.log('============================================================');
    if (issues.length) {
        issues.forEach(i => console.log(`  - [${i.viewport}] ${i.type}: ${i.text}`));
    } else {
        console.log('  无错误,布局正常');
    }
})();