#!/usr/bin/env node
/**
 * 业务流端到端模拟脚本
 * ----------------------
 * 模拟 5 个核心业务场景,验证端到端流程衔接:
 *
 *   Flow 1. 油压订单报工流(领料 → 报工 → 损耗追溯)
 *   Flow 2. 失蜡订单物料分配(批次 → 分配 → 看板更新)
 *   Flow 3. 金料盘点(账面 → 实盘 → 差异回写)
 *   Flow 4. 危化品领用(双人确认 → 库存扣减 → 看板更新)
 *   Flow 5. 环境监测(读数 → 超限 → 报警 → 看板显示)
 *
 * 运行: node tests/ui_preview_business_flow.js
 * 前置: ui_preview 服务在 localhost:8080 运行
 */

const http = require('http');

const HOST = 'localhost';
const PORT = 8080;

let pass = 0;
let fail = 0;
const failures = [];
const flowLog = [];

function request(method, path, body = null) {
    return new Promise((resolve, reject) => {
        const opts = {
            host: HOST, port: PORT, method, path,
            headers: { 'Content-Type': 'application/json' },
        };
        const req = http.request(opts, (res) => {
            let raw = '';
            res.on('data', (c) => (raw += c));
            res.on('end', () => {
                try { resolve({ status: res.statusCode, body: JSON.parse(raw) }); }
                catch (e) { resolve({ status: res.statusCode, body: raw }); }
            });
        });
        req.on('error', reject);
        if (body) req.write(JSON.stringify(body));
        req.end();
    });
}

function check(name, cond, detail = '') {
    if (cond) { pass++; flowLog.push(`  [PASS] ${name}`); }
    else { fail++; failures.push({ name, detail }); flowLog.push(`  [FAIL] ${name} ${detail}`); }
}

function section(title) {
    flowLog.push('');
    flowLog.push(`--- ${title} ---`);
}

// ============================================================
// Flow 1: 油压订单报工流
// ============================================================
async function flow1_oilPressReport() {
    section('Flow 1: 油压订单报工(领料→报工→损耗追溯)');

    // Step 1. 取一条金料批次
    let r = await request('GET', '/api/v1/batch/list');
    check('1.1 取金料批次', r.status === 200 && Array.isArray(r.body.data) && r.body.data.length > 0);
    const batch = r.body.data[0];
    const batchNo = batch.batch_no;
    const initialAvailable = batch.available_weight_g;
    flowLog.push(`  → 选定批次 ${batchNo},可用重量 ${initialAvailable}g`);

    // Step 2. 分配重量
    r = await request('POST', '/api/v1/batch/allocate', { batch_id: batch.id, weight_g: 5.0 });
    check('1.2 分配 5.0g', r.status === 200 && r.body.ok);

    // Step 3. 报工(执模工序,定额损耗 4%)
    r = await request('POST', '/api/v1/workorder_report', {
        production_id: 1,
        operation_id: 1,
        input_weight_g: 5.0,
        output_weight_g: 4.85,   // 3% 损耗,在合理范围内
        output_piece_count: 1,
        work_hours: 0.45,
        operator_id: 8,
        standard_loss_rate: 4.0,
    });
    check('1.3 报工(执模 5.0→4.85)', r.status === 200 && r.body.ok);
    check('  ↳ 损耗 = 0.15g', r.body.data && Math.abs(r.body.data.loss_g - 0.15) < 0.001);
    check('  ↳ 损耗率 = 3%', r.body.data && Math.abs(r.body.data.loss_rate - 3.0) < 0.01);
    check('  ↳ 在 4% 定额内,不超耗', r.body.data && r.body.data.is_over_loss === false);

    // Step 4. 验证损耗可在列表中查到
    r = await request('GET', '/api/v1/workorder_report/list');
    const reports = r.body.data || [];
    const justAdded = reports.find(rep => rep.loss_g === 0.15 && rep.operation === 'OWP06 执模');
    check('1.4 报工在列表可见', !!justAdded);

    flowLog.push(`  → 油压订单报工链路完整 ✓`);
}

// ============================================================
// Flow 2: 失蜡订单物料分配 + 金价
// ============================================================
async function flow2_lostWaxAllocate() {
    section('Flow 2: 失蜡订单物料分配(查询→分配→金价联动)');

    // Step 1. 查询当前金价
    let r = await request('GET', '/api/v1/price/current?gold_type=au9999');
    check('2.1 查询 au9999 金价', r.status === 200 && r.body.ok && typeof r.body.data.price === 'number');
    const oldPrice = r.body.data.price;
    flowLog.push(`  → 当前 Au9999 金价 ¥${oldPrice}/g`);

    // Step 2. 推送新金价
    r = await request('POST', '/api/v1/price/push', {
        source: 'sge', gold_type: 'au9999',
        price_close: 588.0, price_open: 585.0, price_high: 589.0, price_low: 584.0,
    });
    check('2.2 推送新金价 588', r.status === 200 && r.body.ok);

    // Step 3. 失蜡订单分配更多金料(熔金浇铸需要 10-30g)
    r = await request('GET', '/api/v1/batch/list');
    const batch = r.body.data.find(b => b.available_weight_g >= 25);
    if (batch) {
        r = await request('POST', '/api/v1/batch/allocate', { batch_id: batch.id, weight_g: 25.0 });
        check('2.3 失蜡订单分配 25g', r.status === 200 && r.body.ok);
        flowLog.push(`  → 批次 ${batch.batch_no} 分配 25g`);
    } else {
        check('2.3 失蜡订单分配 25g', false, '无可用批次');
    }

    flowLog.push(`  → 失蜡订单物料分配链路完整 ✓`);
}

// ============================================================
// Flow 3: 金料盘点
// ============================================================
async function flow3_inventoryCount() {
    section('Flow 3: 金料盘点(账面→实盘→差异回写)');

    // Step 1. 取两条金料批次
    let r = await request('GET', '/api/v1/batch/list');
    const batches = r.body.data.filter(b => b.available_weight_g > 0).slice(0, 2);
    check('3.1 取 2 条批次', batches.length >= 2);

    // Step 2. 创建盘点单,实盘有差异(故意写不同的 actual)
    const lines = batches.map((b, i) => ({
        batch_id: b.id,
        actual_weight_g: b.net_weight_g + (i === 0 ? 0.05 : -0.03), // +0.05 / -0.03
    }));
    r = await request('POST', '/api/v1/inventory/count', {
        location_id: 1, lines, start: true,
    });
    check('3.2 创建盘点单', r.status === 200 && r.body.ok && r.body.data.name);
    check('  ↳ 盘点单 state=counting', r.body.data && r.body.data.state === 'counting');
    check('  ↳ total_diff_g 自动算', r.body.data && Math.abs(r.body.data.total_diff_g - 0.02) < 0.001);

    // Step 3. 盘点单列表可见
    r = await request('GET', '/api/v1/inventory/list');
    check('3.3 盘点单在列表可见',
        r.body.data.some(c => c.name === r.body.data[0].name));

    flowLog.push(`  → 盘点链路完整 ✓`);
}

// ============================================================
// Flow 4: 危化品领用(双人双锁)
// ============================================================
async function flow4_hazchemIssue() {
    section('Flow 4: 危化品领用(双人确认→库存扣减→看板联动)');

    // Step 1. 取危化品台账
    let r = await request('GET', '/api/v1/hazchem/list');
    const lockRequired = r.body.data.find(c => c.lock_required);
    check('4.1 取 lock_required 危化品', !!lockRequired);
    const initialStock = lockRequired.stock_qty;
    flowLog.push(`  → ${lockRequired.code} 初始库存 ${initialStock}${lockRequired.stock_unit}`);

    // Step 2. 单人确认 → 拒绝
    r = await request('POST', '/api/v1/hazchem/issue', {
        chemical_code: lockRequired.code, qty: 1.0,
        dual_custody_confirmed: false, confirm: true,
    });
    check('4.2 单人确认拒绝', r.status === 400 && r.body.ok === false);

    // Step 3. 双人确认 → 成功,库存 -1
    r = await request('POST', '/api/v1/hazchem/issue', {
        chemical_code: lockRequired.code, qty: 1.0,
        dual_custody_confirmed: true, confirm: true,
    });
    check('4.3 双人确认成功', r.status === 200 && r.body.ok);

    // Step 4. 验证库存减少
    r = await request('GET', '/api/v1/hazchem/list');
    const after = r.body.data.find(c => c.code === lockRequired.code);
    check('4.4 库存扣减 1 单位',
        after && after.stock_qty === initialStock - 1);

    flowLog.push(`  → 危化品领用链路完整 ✓`);
}

// ============================================================
// Flow 5: 环境监测 + 报警
// ============================================================
async function flow5_environmentMonitor() {
    section('Flow 5: 环境监测(读数→超限→报警→看板)');

    // Step 1. 提交正常读数
    let r = await request('POST', '/api/v1/environment/reading', {
        sensor_code: 'ENV-TEMP-01', value: 25.0,
    });
    check('5.1 正常读数 (25℃)', r.body.data.state === 'normal');

    // Step 2. 提交超限读数
    r = await request('POST', '/api/v1/environment/reading', {
        sensor_code: 'ENV-TEMP-01', value: 65.0,
    });
    check('5.2 超限读数 (65℃) 触发报警', r.body.data.state === 'alarm');
    check('  ↳ alarm_desc 描述超限', r.body.data.alarm_desc && r.body.data.alarm_desc.length > 0);

    // Step 3. 验证报警在列表中可见
    r = await request('GET', '/api/v1/environment/alarms');
    check('5.3 报警在 alarms 列表',
        r.body.data.some(a => a.value === 65.0));

    // Step 4. 最新读数显示报警状态
    r = await request('GET', '/api/v1/environment/latest');
    check('5.4 latest 包含报警传感器',
        r.body.data.some(s => s.value === 65.0 && s.state === 'alarm'));

    flowLog.push(`  → 环境监测链路完整 ✓`);
}

// ============================================================
// Flow 6: 设备状态流转(heartbeat + metric)
// ============================================================
async function flow6_deviceState() {
    section('Flow 6: 设备状态流转');

    // Step 1. 设备列表
    let r = await request('GET', '/api/v1/device/list');
    const equip = r.body.data[0];  // OBP-001
    check('6.1 取设备', !!equip);
    flowLog.push(`  → 设备 ${equip.code} 当前 state=${equip.state}`);

    // Step 2. 心跳上报 running
    r = await request('POST', '/api/v1/device/heartbeat', {
        device_code: equip.code, state: 'running',
        runtime_hours: 100, downtime_hours: 10,
    });
    check('6.2 心跳 state=running', r.body.ok && r.body.data.new_state === 'running');

    // Step 3. 度量上报
    r = await request('POST', '/api/v1/device/metric', {
        device_code: equip.code, metrics: { temperature_c: 850, weight_g: 5.123 },
    });
    check('6.3 metric 上报', r.body.ok);

    flowLog.push(`  → 设备链路完整 ✓`);
}

// ============================================================
// Flow 7: 看板 KPI 反映所有操作
// ============================================================
async function flow7_dashboardAggregates() {
    section('Flow 7: 看板 KPI 汇总验证');

    // Step 1. 取 KPI
    let r = await request('GET', '/api/v1/dashboard/kpi');
    check('7.1 KPI 可拉取', r.status === 200 && r.body.ok);
    const kpi = r.body.data;
    flowLog.push(`  → today=${kpi.today} done=${kpi.done_today} in_progress=${kpi.in_progress}`);
    flowLog.push(`  → over_loss=${kpi.over_loss_count} critical_mold=${kpi.critical_mold_count}`);
    flowLog.push(`  → oil_press=${kpi.oil_press_orders} lost_wax=${kpi.lost_wax_orders}`);
    flowLog.push(`  → gold_price=¥${kpi.current_gold_price} total_value=¥${kpi.total_value.toFixed(2)}`);

    // Step 2. 验证 KPI 字段完整性
    const required = ['today', 'done_today', 'in_progress', 'over_loss_count',
                      'critical_mold_count', 'oil_press_orders', 'lost_wax_orders',
                      'current_gold_price', 'total_value', 'avg_loss_rate'];
    for (const f of required) {
        check(`  ↳ KPI 含 ${f}`, kpi[f] !== undefined);
    }
}

// ============================================================
// 主函数
// ============================================================
(async () => {
    console.log('============================================================');
    console.log('业务流端到端模拟');
    console.log('============================================================');

    try {
        await flow1_oilPressReport();
        await flow2_lostWaxAllocate();
        await flow3_inventoryCount();
        await flow4_hazchemIssue();
        await flow5_environmentMonitor();
        await flow6_deviceState();
        await flow7_dashboardAggregates();
    } catch (e) {
        console.error('FATAL:', e.message);
        process.exit(1);
    }

    flowLog.forEach(l => console.log(l));
    console.log('\n============================================================');
    console.log(`结果: ${pass} passed, ${fail} failed`);
    console.log('============================================================');
    if (fail > 0) {
        console.log('\n失败明细:');
        failures.forEach(f => console.log(`  - ${f.name}: ${f.detail}`));
        process.exit(1);
    }
    process.exit(0);
})();