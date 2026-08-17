// 敦煌金 ERP - 前端预览服务器 (静态文件 + Mock REST API 一体)
// 启动: node server.js  →  http://localhost:8080
// 前端页面从 /pages/* 加载, 数据从 /api/v1/* 读写 (内存 mock)
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const ROOT = __dirname;
const PORT = process.env.PORT || 8080;
const db = require('./mock-data');

const MIME = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
};

// ---------- 通用 ----------
function json(res, obj, status = 200) {
    const body = JSON.stringify(obj);
    res.writeHead(status, {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    });
    res.end(body);
}
const ok = (res, data = {}, msg = 'ok') => json(res, { ok: true, msg, data });
const err = (res, msg, status = 400) => json(res, { ok: false, error: msg }, status);

function readBody(req) {
    return new Promise((resolve) => {
        let raw = '';
        req.on('data', (c) => (raw += c));
        req.on('end', () => {
            try { resolve(JSON.parse(raw || '{}')); }
            catch (e) { resolve({}); }
        });
    });
}

// ---------- API 路由 ----------
async function apiHandler(req, res, pathname, query) {
    const method = req.method;
    const p = pathname.replace(/^\/api\/v1\//, '');
    const parts = p.split('/').filter(Boolean);

    // 认证
    if (p === 'login' && method === 'POST') {
        return ok(res, { uid: 8, name: '张三', groups: ['车间班组长'] });
    }
    // 看板 KPI
    if (p === 'dashboard/kpi' && method === 'GET') {
        return ok(res, db.computeKpi());
    }
    // 金价
    if (p === 'price/current' && method === 'GET') {
        return ok(res, { gold_type: 'au9999', source: 'sge', price: 582.50, timestamp: '2026-08-05 10:30:00' });
    }
    if (p === 'price/push' && method === 'POST') {
        return ok(res, { id: db.nextId(), name: new Date().toISOString() });
    }

    // 设备
    if (p === 'device/list' && method === 'GET') {
        return ok(res, db.equipment);
    }
    if (p === 'device/heartbeat' && method === 'POST') {
        const b = await readBody(req);
        const eq = db.equipment.find((e) => e.code === b.device_code);
        if (!eq) return err(res, '设备不存在', 404);
        if (b.state) eq.state = b.state;
        return ok(res, { device_code: eq.code, new_state: eq.state, oee: eq.oee });
    }
    if (p === 'device/metric' && method === 'POST') {
        const b = await readBody(req);
        const eq = db.equipment.find((e) => e.code === b.device_code);
        if (!eq) return err(res, '设备不存在', 404);
        if (eq.state === 'idle') eq.state = 'running';
        return ok(res, { device_code: b.device_code, metrics_received: Object.keys(b.metrics || {}) });
    }

    // 金料批次
    if (p === 'batch/list' && method === 'GET') {
        return ok(res, db.batches);
    }
    if (parts[0] === 'batch' && parts[1] === 'allocate' && method === 'POST') {
        const b = await readBody(req);
        const batch = db.batches.find((x) => x.id === Number(b.batch_id));
        if (!batch) return err(res, '批次不存在', 404);
        if (b.weight_g > batch.available_weight_g) return err(res, '可用重量不足');
        batch.available_weight_g -= b.weight_g;
        batch.allocated_weight_g += b.weight_g;
        return ok(res, { id: batch.id, available_weight_g: batch.available_weight_g, allocated_weight_g: batch.allocated_weight_g });
    }
    if (parts[0] === 'batch' && parts[1] && method === 'GET') {
        const batch = db.batches.find((x) => x.batch_no === parts[1]);
        if (!batch) return err(res, '批次不存在', 404);
        return ok(res, batch);
    }

    // 印记 OCR 校验 (Phase 2.3 补 mock)
    if (p === 'imprint/verify' && method === 'POST') {
        const b = await readBody(req);
        const imprint_id = b.imprint_id;
        if (!imprint_id) return err(res, 'imprint_id required');
        // 模拟 imprint: 取 demo 内容
        const expectedContent = `Au 999 XX`;
        const verified = true;
        const mismatch = b.expected && expectedContent !== b.expected;
        const passed = !mismatch;
        return ok(res, {
            id: imprint_id,
            verified,
            mismatch,
            content: expectedContent,
            passed,
        });
    }

    // XRF 检测 (Phase 2.3 补 mock)
    if (p === 'xrf/save' && method === 'POST') {
        const b = await readBody(req);
        const gold_pct = Number(b.gold_pct || 0);
        const standard_pct = Number(b.standard_pct || 99.0);
        const main_metal_pct = gold_pct;
        const is_passed = gold_pct >= standard_pct;
        return ok(res, {
            id: db.nextId(),
            is_passed,
            main_metal_pct,
        });
    }

    // 工序报工
    if (p === 'workorder_report/list' && method === 'GET') {
        return ok(res, db.workorderReports);
    }
    if (p === 'workorder_report' && method === 'POST') {
        const b = await readBody(req);
        // Phase 2.3 测试补强:必填字段校验
        const required = ['production_id', 'operation_id', 'input_weight_g', 'output_weight_g'];
        for (const k of required) {
            if (b[k] === undefined || b[k] === null) {
                return err(res, `字段缺失: ${k}`);
            }
        }
        const loss_g = Math.max(0, (b.input_weight_g || 0) - (b.output_weight_g || 0));
        const loss_rate = b.input_weight_g > 0 ? (loss_g / b.input_weight_g) * 100 : 0;
        const std = b.standard_loss_rate || 0;
        const loss_diff_pct = loss_rate - std;
        const rec = {
            id: db.nextId(),
            name: 'BG' + new Date().toISOString().slice(0, 10).replace(/-/g, '') + '-' + String(db.workorderReports.length + 1).padStart(5, '0'),
            production: b.production_name || 'MO-00425',
            operation: b.operation_name || 'OWP06 执模',
            workstation: b.workstation_name || 'WS-OWP',
            operator: b.operator || '张三',
            input_weight_g: Number(Number(b.input_weight_g).toFixed(3)), output_weight_g: Number(Number(b.output_weight_g).toFixed(3)),
            loss_g: Number(loss_g.toFixed(3)), loss_rate: Number(loss_rate.toFixed(4)),
            standard_loss_rate: std, loss_diff_pct: Number(loss_diff_pct.toFixed(4)),
            is_over_loss: Math.abs(loss_diff_pct) > 20,
            quality_state: b.quality_state || 'passed',
            report_time: b.report_time || '2026-08-05 ' + new Date().toTimeString().slice(0, 5),
        };
        db.workorderReports.unshift(rec);
        return ok(res, { id: rec.id, name: rec.name, loss_g: rec.loss_g, loss_rate: rec.loss_rate, loss_diff_pct: rec.loss_diff_pct, is_over_loss: rec.is_over_loss });
    }

    // 环境
    if (p === 'environment/latest' && method === 'GET') {
        return ok(res, db.environmentReadings);
    }
    if (p === 'environment/alarms' && method === 'GET') {
        return ok(res, db.environmentReadings.filter((r) => r.state === 'alarm'));
    }
    if (p === 'environment/reading' && method === 'POST') {
        const b = await readBody(req);
        const sensor = db.environmentSensors.find((s) => s.code === b.sensor_code);
        if (!sensor) return err(res, '传感器不存在', 404);
        let state = 'normal', alarm_desc = '';
        if (sensor.alarm_min > 0 && b.value < sensor.alarm_min) { state = 'alarm'; alarm_desc = '低于下限 ' + sensor.alarm_min + ' ' + sensor.unit; }
        if (sensor.alarm_max > 0 && b.value > sensor.alarm_max) { state = 'alarm'; alarm_desc = '超过上限 ' + sensor.alarm_max + ' ' + sensor.unit; }
        const rec = { id: db.nextId(), sensor_code: sensor.code, sensor_name: sensor.name, sensor_type: sensor.sensor_type, value: b.value, unit: sensor.unit, state, alarm_desc, reading_time: new Date().toISOString().slice(0, 16).replace('T', ' ') };
        const idx = db.environmentReadings.findIndex((r) => r.sensor_code === sensor.code);
        if (idx >= 0) db.environmentReadings[idx] = rec; else db.environmentReadings.push(rec);
        return ok(res, { id: rec.id, state, alarm_desc });
    }

    // 危化品
    if (p === 'hazchem/list' && method === 'GET') {
        return ok(res, db.hazardousChemicals);
    }
    if (p === 'hazchem/issue' && method === 'POST') {
        const b = await readBody(req);
        const chem = db.hazardousChemicals.find((c) => c.code === b.chemical_code);
        if (!chem) return err(res, '危化品不存在', 404);
        if (chem.lock_required && !b.dual_custody_confirmed) return err(res, '危化品需双人确认后方可领用');
        if (b.qty > chem.stock_qty) return err(res, '库存不足');
        chem.stock_qty -= b.qty;
        return ok(res, { id: db.nextId(), name: 'WH20260805-' + String(db.nextId()), state: 'confirmed' });
    }

    // 能耗
    if (p === 'energy/latest' && method === 'GET') {
        return ok(res, db.energyMeters);
    }
    if (p === 'energy/reading' && method === 'POST') {
        const b = await readBody(req);
        const meter = db.energyMeters.find((m) => m.code === b.meter_code);
        if (!meter) return err(res, '表计不存在', 404);
        const prev = meter.cumulative_value;
        meter.cumulative_value = b.cumulative_value;
        meter.period_consumption = Math.max(0, b.cumulative_value - prev);
        meter.period_amount = meter.period_consumption * 0.7;
        return ok(res, { id: db.nextId(), period_consumption: meter.period_consumption, period_amount: meter.period_amount });
    }

    // 维护
    if (p === 'maintenance/list' && method === 'GET') {
        return ok(res, db.maintenanceOrders);
    }
    if (p === 'maintenance/order' && method === 'POST') {
        const b = await readBody(req);
        const rec = { id: db.nextId(), name: 'WX20260805-' + String(db.maintenanceOrders.length + 1).padStart(5, '0'), equipment: b.equipment_code || '—', maintenance_type: b.maintenance_type || 'cm', priority: b.priority || '1', state: 'draft', assignee: b.assignee || '', planned_date: b.planned_date || '2026-08-05', duration_hours: null, maintenance_cost: null };
        db.maintenanceOrders.unshift(rec);
        return ok(res, { id: rec.id, name: rec.name, state: rec.state });
    }
    if (p === 'spare_part/list' && method === 'GET') {
        return ok(res, db.spareParts);
    }

    // 资质
    if (p === 'certificate/list' && method === 'GET') {
        return ok(res, db.certificates);
    }
    if (p === 'certificate/verify' && method === 'GET') {
        const certs = db.certificates.filter((c) => c.is_valid);
        return ok(res, { user_id: Number(query.user_id || 8), cert_type: query.cert_type || null, qualified: certs.length > 0, certificates: certs });
    }
    if (p === 'attendance/list' && method === 'GET') {
        return ok(res, db.attendance);
    }

    // SOP / ECN
    if (p === 'sop/list' && method === 'GET') return ok(res, db.sops);
    if (p === 'ecn/list' && method === 'GET') return ok(res, db.ecns);

    // 生产后: 盘点
    if (p === 'inventory/list' && method === 'GET') {
        return ok(res, db.inventoryCounts.map((c) => ({ id: c.id, name: c.name, inventory_date: c.inventory_date, state: c.state, total_book_weight_g: c.total_book_weight_g, total_actual_weight_g: c.total_actual_weight_g, total_diff_g: c.total_diff_g })));
    }
    if (p === 'inventory/count' && method === 'POST') {
        const b = await readBody(req);
        const lines = (b.lines || []).map((l) => {
            const batch = db.batches.find((x) => x.id === Number(l.batch_id));
            const book = batch ? batch.net_weight_g : 0;
            const actual = l.actual_weight_g || 0;
            return { batch_no: batch ? batch.batch_no : '—', product: batch ? batch.product : '—', book_weight_g: book, actual_weight_g: actual, diff_g: Number((actual - book).toFixed(3)), result: Math.abs(actual - book) < 0.0005 ? '平账' : (actual - book < 0 ? '盘亏' : '盘盈') };
        });
        const total_book = lines.reduce((s, l) => s + l.book_weight_g, 0);
        const total_actual = lines.reduce((s, l) => s + l.actual_weight_g, 0);
        const rec = { id: db.nextId(), name: 'PD20260805-' + String(db.inventoryCounts.length + 1).padStart(5, '0'), inventory_date: b.inventory_date || '2026-08-05', state: b.start ? 'counting' : 'draft', counter: '张三', reviewer: b.reviewer || null, total_book_weight_g: Number(total_book.toFixed(3)), total_actual_weight_g: Number(total_actual.toFixed(3)), total_diff_g: Number((total_actual - total_book).toFixed(3)), lines };
        db.inventoryCounts.unshift(rec);
        return ok(res, { id: rec.id, name: rec.name, state: rec.state, total_diff_g: rec.total_diff_g });
    }

    // 生产后: 成品入库
    if (p === 'finished_goods/list' && method === 'GET') {
        return ok(res, db.finishedGoods);
    }
    if (p === 'finished_goods/post' && method === 'POST') {
        const b = await readBody(req);
        const sns = b.piece_sns || [];
        const lines = sns.map((sn, i) => ({ sn, style: '18K 钻石戒指', purity: 'Au750', weight_g: 5.180, imprint: '合格', qc: '通过', ngtc: 'NGTC-88' + (200 + i), state: '已入库' }));
        const rec = { id: db.nextId(), name: 'CP20260805-' + String(db.finishedGoods.length + 1).padStart(5, '0'), post_date: '2026-08-05', state: 'posted', generate_batch: !!b.generate_batch, total_piece_count: lines.length, total_weight_g: Number((lines.length * 5.180).toFixed(3)), lines };
        db.finishedGoods.unshift(rec);
        return ok(res, { id: rec.id, name: rec.name, state: rec.state, total_piece_count: rec.total_piece_count, total_weight_g: rec.total_weight_g, batch_id: null });
    }

    // 生产后: 班后回料
    if (p === 'material_return/list' && method === 'GET') {
        return ok(res, db.materialReturns);
    }
    if (p === 'material_return/confirm' && method === 'POST') {
        const b = await readBody(req);
        const rec = { id: db.nextId(), name: 'HL20260805-' + String(db.materialReturns.length + 1).padStart(5, '0'), return_date: '2026-08-05', return_source: b.return_source || 'gate', material_type: b.material_type || 'gold', product: b.product_name || '足金 9999', weight_g: b.weight_g, target: b.create_new_batch === false ? '回入现有批次' : '新批次', report: null, state: 'confirmed' };
        db.materialReturns.unshift(rec);
        return ok(res, { id: rec.id, name: rec.name, state: rec.state, batch_id: db.nextId() });
    }

    // 未匹配
    return err(res, '接口不存在: ' + pathname, 404);
}

// ---------- 静态文件 ----------
function serveStatic(res, pathname) {
    let urlPath = decodeURIComponent(pathname.split('?')[0]);
    if (urlPath === '/') urlPath = '/index.html';
    const filePath = path.resolve(ROOT, '.' + urlPath);
    if (!filePath.startsWith(ROOT)) {
        res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('403 Forbidden');
        return;
    }
    fs.readFile(filePath, (error, data) => {
        if (error) {
            res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
            res.end('404 Not Found');
            return;
        }
        const ext = path.extname(filePath).toLowerCase();
        res.writeHead(200, {
            'Content-Type': MIME[ext] || 'application/octet-stream',
            'Cache-Control': 'no-store, no-cache, must-revalidate',
        });
        res.end(data);
    });
}

// ---------- 主服务 ----------
http.createServer((req, res) => {
    if (req.method === 'OPTIONS') {
        res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' });
        res.end();
        return;
    }
    const parsed = url.parse(req.url, true);
    if (parsed.pathname.startsWith('/api/')) {
        apiHandler(req, res, parsed.pathname, parsed.query).catch((e) => err(res, String(e), 500));
    } else {
        serveStatic(res, req.url);
    }
}).listen(PORT, () => {
    console.log(`敦煌金 ERP 预览已启动: http://localhost:${PORT}`);
    console.log(`  - 静态页面: http://localhost:${PORT}/`);
    console.log(`  - Mock API: http://localhost:${PORT}/api/v1/dashboard/kpi`);
});
