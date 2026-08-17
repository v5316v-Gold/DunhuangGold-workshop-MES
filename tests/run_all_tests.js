#!/usr/bin/env node
/**
 * 一键全跑测试
 * --------------
 * 依次执行:
 *   L1: API 烟测(67 assertions)
 *   L3: 业务流模拟(38 assertions)
 *   L2: 手动 UI checklist(需人工)
 *
 * 运行: node tests/run_all_tests.js
 */

const { spawn } = require('child_process');
const path = require('path');

const tests = [
    { name: 'L1 API 烟测', script: 'ui_preview_api_smoke.js' },
    { name: 'L3 业务流模拟', script: 'ui_preview_business_flow.js' },
];

function runScript(script) {
    return new Promise((resolve) => {
        console.log(`\n>>> 运行 ${script} ...`);
        const proc = spawn('node', [path.join(__dirname, script)], { stdio: 'inherit' });
        proc.on('close', (code) => {
            resolve(code);
        });
    });
}

(async () => {
    console.log('============================================================');
    console.log('ui_preview 全套测试');
    console.log('============================================================');
    console.log('前置: ui_preview 服务必须运行在 localhost:8080');

    let allPass = true;
    const results = [];

    for (const test of tests) {
        const code = await runScript(test.script);
        results.push({ name: test.name, exitCode: code });
        if (code !== 0) allPass = false;
    }

    console.log('\n\n============================================================');
    console.log('总报告');
    console.log('============================================================');
    results.forEach(r => {
        const mark = r.exitCode === 0 ? '✓' : '✗';
        console.log(`  ${mark} ${r.name} (exit=${r.exitCode})`);
    });

    console.log('\n--- L2 手动测试 ---');
    console.log('见 tests/ui_checklist.md(共 144 个检查点)');
    console.log('打开浏览器访问 http://localhost:8080 逐项验证');

    console.log('\n============================================================');
    if (allPass) {
        console.log('[PASS] 自动测试全部通过,可继续 L2 手动验证');
        process.exit(0);
    } else {
        console.log('[FAIL] 有测试失败,见上方输出');
        process.exit(1);
    }
})();