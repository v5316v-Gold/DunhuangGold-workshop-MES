// 敦煌金 ERP - 页面动态渲染器
// 每个页面加载后调用对应 renderer(main)，fetch 真实(mock)数据并渲染 + 绑定交互

window.RENDERERS = {};

const { get, post } = window.API;
const U = window.UI;

// 加载失败兜底
async function safeFetch(main, path) {
    try { return await get(path); }
    catch (e) { main.innerHTML = U.notice('danger', '❌ 数据加载失败: ' + e.message); return null; }
}

// ============ 车间看板 ============
window.RENDERERS.dashboard = async function (main) {
    const k = await safeFetch(main, '/dashboard/kpi');
    if (!k) return;
    main.innerHTML = U.pageHeader('车间看板', '<button class="btn" onclick="location.reload()">🔄 刷新</button>') +
        U.kpiCards([
            { label: '当日完工', value: k.done_today, sub: '件级 SN 已入库', success: true },
            { label: '进行中', value: k.in_progress, sub: '生产订单' },
            { label: '超耗预警', value: k.over_loss_count, sub: '需复盘', danger: k.over_loss_count > 0 },
            { label: '当前金价', value: '¥ ' + k.current_gold_price, sub: 'Au9999 SGE', gold: true },
        ]) +
        U.kpiCards([
            { label: '库存估值', value: U.money(k.total_value), sub: '按当前金价' },
            { label: '平均损耗率', value: k.avg_loss_rate + '%', sub: '今日' },
            { label: 'XRF 合格率', value: k.xrf_passed_pct + '%', sub: k.xrf_count_today + ' 次检测' },
            { label: '油压 / 失蜡', value: k.oil_press_orders + ' / ' + k.lost_wax_orders, sub: '进行中订单' },
        ]) +
        U.notice('info', '📊 数据来自 <code>/api/v1/dashboard/kpi</code>（实时聚合），点击左侧菜单切换模块。');
};

// ============ 金料批次 ============
window.RENDERERS.material_batch = async function (main) {
    const rows = await safeFetch(main, '/batch/list');
    if (!rows) return;
    const totalNet = rows.reduce((s, r) => s + r.net_weight_g, 0);
    const totalAvail = rows.reduce((s, r) => s + r.available_weight_g, 0);
    main.innerHTML = U.pageHeader('金料批次', '<button class="btn" onclick="window.window.RENDERERS.material_batch(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.kpiCards([
            { label: '可用库存', value: U.num(totalAvail, 3) + ' g', sub: U.money(rows.reduce((s, r) => s + r.current_value, 0)), gold: true },
            { label: '批次总数', value: rows.length, sub: '精度 0.001g' },
            { label: '待检验', value: rows.filter((r) => r.inspection_state === 'pending').length, sub: '100% 已检' },
        ]) +
        U.renderTable(
            [
                { label: '批次号', key: 'batch_no' }, { label: '物料', key: 'product' }, { label: '成色', key: 'purity', render: (v) => v + '%' },
                { label: '净重 (g)', key: 'net_weight_g', num: true, digits: 3 }, { label: '可用 (g)', key: 'available_weight_g', num: true, digits: 3 },
                { label: '已消耗 (g)', key: 'consumed_weight_g', num: true, digits: 3 }, { label: '当前价值', key: 'current_value', money: true },
                { label: '状态', key: 'state', badge: true },
            ],
            rows,
            `<td colspan="5">合计</td><td class="number">${U.num(totalNet, 3)}</td><td class="number">${U.num(totalAvail, 3)}</td><td colspan="2"></td>`
        );
};

// ============ 工序报工 ============
window.RENDERERS.workorder_report = async function (main) {
    const rows = await safeFetch(main, '/workorder_report/list');
    if (!rows) return;
    const totalInput = rows.reduce((s, r) => s + r.input_weight_g, 0);
    const totalOutput = rows.reduce((s, r) => s + r.output_weight_g, 0);
    const over = rows.filter((r) => r.is_over_loss).length;
    main.innerHTML = U.pageHeader('工序报工', '<button class="btn" onclick="window.window.RENDERERS.workorder_report(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.kpiCards([
            { label: '今日报工', value: rows.length, sub: '合格 ' + rows.filter((r) => r.quality_state === 'passed').length, success: true },
            { label: '超耗预警', value: over, sub: '需复盘', danger: over > 0 },
            { label: '总投料', value: U.num(totalInput, 3) + ' g', sub: '总产出 ' + U.num(totalOutput, 3) + ' g' },
        ]) +
        `<div class="card"><div class="card-header"><h3>报工录入</h3></div><div class="card-body">
            <div class="row" style="gap:12px; flex-wrap:wrap;">
                <label>工序 <input id="wr-op" value="OWP06 执模" style="width:150px"></label>
                <label>操作员 <input id="wr-operator" value="张三" style="width:120px"></label>
                <label>投料(g) <input id="wr-in" type="number" step="0.001" value="5.250" style="width:110px"></label>
                <label>产出(g) <input id="wr-out" type="number" step="0.001" value="5.180" style="width:110px"></label>
                <label>质量 <select id="wr-quality" style="width:110px"><option>合格</option><option>不合格</option><option>返工</option></select></label>
                <button class="btn btn-primary" id="wr-submit">➕ 提交报工</button>
            </div>
        </div></div>` +
        U.renderTable(
            [
                { label: '报工单', key: 'name' }, { label: '时间', key: 'report_time' }, { label: '订单', key: 'production' }, { label: '工序', key: 'operation' },
                { label: '操作员', key: 'operator' }, { label: '投料 (g)', key: 'input_weight_g', num: true, digits: 3 }, { label: '产出 (g)', key: 'output_weight_g', num: true, digits: 3 },
                { label: '损耗 (g)', key: 'loss_g', num: true, digits: 3 }, { label: '损耗率', key: 'loss_rate', render: (v, r) => `<span class="number ${r.is_over_loss ? 'text-danger' : ''}">${v}%</span>` },
                { label: '质量', key: 'quality_state', badge: true },
            ],
            rows.map((r) => ({ ...r, _danger: r.is_over_loss }))
        );
    document.getElementById('wr-submit').onclick = async () => {
        try {
            const res = await post('/workorder_report', {
                operation_name: document.getElementById('wr-op').value,
                operator: document.getElementById('wr-operator').value,
                input_weight_g: Number(document.getElementById('wr-in').value),
                output_weight_g: Number(document.getElementById('wr-out').value),
                quality_state: document.getElementById('wr-quality').value === '合格' ? 'passed' : (document.getElementById('wr-quality').value === '返工' ? 'rework' : 'failed'),
            });
            U.toast('报工成功 ' + res.name + '，损耗率 ' + res.loss_rate + '%');
            window.RENDERERS.workorder_report(main);
        } catch (e) { U.toast(e.message, 'error'); }
    };
};

// ============ 金料盘点单 ============
window.RENDERERS.inventory_count = async function (main) {
    const rows = await safeFetch(main, '/inventory/list');
    if (!rows) return;
    const cur = await get('/batch/list');
    main.innerHTML = U.pageHeader('金料盘点单', '<button class="btn" onclick="window.window.RENDERERS.inventory_count(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        `<div class="card"><div class="card-header"><h3>新建盘点</h3></div><div class="card-body">
            <div class="row" style="gap:12px; flex-wrap:wrap;">
                <label>批次 <select id="ic-batch" style="width:220px">${cur.map((b) => `<option value="${b.id}">${b.batch_no} (${b.product})</option>`).join('')}</select></label>
                <label>实盘重量(g) <input id="ic-actual" type="number" step="0.001" value="0" style="width:120px"></label>
                <button class="btn btn-primary" id="ic-submit">➕ 开始盘点</button>
            </div>
        </div></div>` +
        U.renderTable(
            [
                { label: '盘点单号', key: 'name' }, { label: '盘点日期', key: 'inventory_date' }, { label: '状态', key: 'state', badge: true },
                { label: '账面合计 (g)', key: 'total_book_weight_g', num: true, digits: 3 }, { label: '实盘合计 (g)', key: 'total_actual_weight_g', num: true, digits: 3 },
                { label: '差异合计 (g)', key: 'total_diff_g', render: (v) => `<span class="number ${v < 0 ? 'text-danger' : ''}">${v}</span>` },
            ],
            rows.map((r) => ({ ...r, _danger: r.total_diff_g < -0.0005 }))
        ) +
        U.notice('info', '📋 流程：<strong>草稿 → 开始盘点(锁定批次) → 录入实盘 → 复核 → 过账(差异回写批次)</strong>。下方表单会调用 <code>POST /inventory/count</code> 创建盘点单。');
    document.getElementById('ic-submit').onclick = async () => {
        try {
            const batchId = Number(document.getElementById('ic-batch').value);
            const actual = Number(document.getElementById('ic-actual').value);
            const res = await post('/inventory/count', { lines: [{ batch_id: batchId, actual_weight_g: actual }], start: true });
            U.toast('盘点单 ' + res.name + ' 已创建（状态 ' + res.state + '）');
            window.RENDERERS.inventory_count(main);
        } catch (e) { U.toast(e.message, 'error'); }
    };
};

// ============ 班后回料单 ============
window.RENDERERS.material_return = async function (main) {
    const rows = await safeFetch(main, '/material_return/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('班后回料单', '<button class="btn" onclick="window.window.RENDERERS.material_return(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        `<div class="card"><div class="card-header"><h3>回料录入</h3></div><div class="card-body">
            <div class="row" style="gap:12px; flex-wrap:wrap;">
                <label>来源 <select id="mr-source" style="width:130px"><option value="gate">浇口料</option><option value="scrap_edge">边角料</option><option value="polish_powder">抛光粉</option></select></label>
                <label>物料 <input id="mr-product" value="足金 9999" style="width:130px"></label>
                <label>重量(g) <input id="mr-weight" type="number" step="0.001" value="1.0" style="width:110px"></label>
                <button class="btn btn-primary" id="mr-submit">➕ 回库</button>
            </div>
        </div></div>` +
        U.renderTable(
            [
                { label: '回料单号', key: 'name' }, { label: '日期', key: 'return_date' }, { label: '来源', key: 'return_source' },
                { label: '物料', key: 'product' }, { label: '重量 (g)', key: 'weight_g', num: true, digits: 3 }, { label: '去向', key: 'target' },
                { label: '状态', key: 'state', badge: true },
            ],
            rows
        );
    document.getElementById('mr-submit').onclick = async () => {
        try {
            const res = await post('/material_return/confirm', {
                return_source: document.getElementById('mr-source').value,
                product_name: document.getElementById('mr-product').value,
                weight_g: Number(document.getElementById('mr-weight').value),
                create_new_batch: true,
            });
            U.toast('回料成功 ' + res.name);
            window.RENDERERS.material_return(main);
        } catch (e) { U.toast(e.message, 'error'); }
    };
};

// ============ 成品入库单 ============
window.RENDERERS.finished_goods = async function (main) {
    const rows = await safeFetch(main, '/finished_goods/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('成品入库单', '<button class="btn" onclick="window.window.RENDERERS.finished_goods(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        `<div class="card"><div class="card-header"><h3>扫码入库 (按件级 SN)</h3></div><div class="card-body">
            <div class="row" style="gap:12px; flex-wrap:wrap;">
                <label>SN 列表 (逗号分隔) <input id="fg-sns" value="GLD-20260805-RING-0101, GLD-20260805-RING-0102" style="width:340px"></label>
                <button class="btn btn-primary" id="fg-submit">📦 入库</button>
            </div>
        </div></div>` +
        U.renderTable(
            [
                { label: '入库单号', key: 'name' }, { label: '日期', key: 'post_date' }, { label: '件数', key: 'total_piece_count', num: true, digits: 0 },
                { label: '总重量 (g)', key: 'total_weight_g', num: true, digits: 3 }, { label: '生成批次', key: 'generate_batch', render: (v) => v ? '是' : '否' },
                { label: '状态', key: 'state', badge: true },
            ],
            rows
        );
    document.getElementById('fg-submit').onclick = async () => {
        try {
            const sns = document.getElementById('fg-sns').value.split(',').map((s) => s.trim()).filter(Boolean);
            const res = await post('/finished_goods/post', { piece_sns: sns, generate_batch: false });
            U.toast('入库成功 ' + res.name + '，共 ' + res.total_piece_count + ' 件');
            window.RENDERERS.finished_goods(main);
        } catch (e) { U.toast(e.message, 'error'); }
    };
};

// ============ 设备台账 ============
window.RENDERERS.equipment = async function (main) {
    const rows = await safeFetch(main, '/device/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('设备台账', '<button class="btn" onclick="window.window.RENDERERS.equipment(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.renderTable(
            [
                { label: '编号', key: 'code' }, { label: '名称', key: 'name' }, { label: '类别', key: 'category' },
                { label: '协议', key: 'protocol' }, { label: 'IP', key: 'ip' }, { label: 'OEE', key: 'oee', render: (v) => v ? v + '%' : '—' },
                { label: '状态', key: 'state', badge: true },
            ],
            rows
        );
};

// ============ 环境监测 ============
window.RENDERERS.environment = async function (main) {
    const rows = await safeFetch(main, '/environment/latest');
    if (!rows) return;
    const alarms = rows.filter((r) => r.state === 'alarm').length;
    main.innerHTML = U.pageHeader('环境监测', '<button class="btn" onclick="window.window.RENDERERS.environment(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.kpiCards([
            { label: '超限报警', value: alarms, sub: '需处理', danger: alarms > 0 },
            { label: '在线传感器', value: rows.length, sub: '实时读数' },
        ]) +
        `<div class="card"><div class="card-header"><h3>上报读数</h3></div><div class="card-body">
            <div class="row" style="gap:12px; flex-wrap:wrap;">
                <label>传感器 <select id="env-code" style="width:200px">${rows.map((r) => `<option value="${r.sensor_code}">${r.sensor_code} ${r.sensor_name}</option>`).join('')}</select></label>
                <label>读数 <input id="env-value" type="number" step="0.01" value="25.0" style="width:100px"></label>
                <button class="btn btn-primary" id="env-submit">📡 上报</button>
            </div>
        </div></div>` +
        U.renderTable(
            [
                { label: '传感器', key: 'sensor_code' }, { label: '点位', key: 'sensor_name' }, { label: '类型', key: 'sensor_type' },
                { label: '读数', key: 'value', num: true, digits: 2 }, { label: '单位', key: 'unit' }, { label: '状态', key: 'state', badge: true },
                { label: '说明', key: 'alarm_desc' }, { label: '时间', key: 'reading_time' },
            ],
            rows.map((r) => ({ ...r, _danger: r.state === 'alarm' }))
        );
    document.getElementById('env-submit').onclick = async () => {
        try {
            const res = await post('/environment/reading', { sensor_code: document.getElementById('env-code').value, value: Number(document.getElementById('env-value').value) });
            U.toast('读数已上报，状态：' + res.state + (res.alarm_desc ? '（' + res.alarm_desc + '）' : ''));
            window.RENDERERS.environment(main);
        } catch (e) { U.toast(e.message, 'error'); }
    };
};

// ============ 危化品 ============
window.RENDERERS.hazardous_chemical = async function (main) {
    const rows = await safeFetch(main, '/hazchem/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('危化品管理', '<button class="btn" onclick="window.window.RENDERERS.hazardous_chemical(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        `<div class="card"><div class="card-header"><h3>领用出库 (双人双锁)</h3></div><div class="card-body">
            <div class="row" style="gap:12px; flex-wrap:wrap;">
                <label>危化品 <select id="hc-code" style="width:200px">${rows.map((c) => `<option value="${c.code}">${c.code} ${c.name}</option>`).join('')}</select></label>
                <label>数量 <input id="hc-qty" type="number" step="0.1" value="10" style="width:100px"></label>
                <label><input type="checkbox" id="hc-dual" checked> 双人确认</label>
                <button class="btn btn-primary" id="hc-submit">🔒 领用</button>
            </div>
        </div></div>` +
        U.renderTable(
            [
                { label: '编号', key: 'code' }, { label: '名称', key: 'name' }, { label: '类别', key: 'category' }, { label: '危险等级', key: 'danger_level', badge: true },
                { label: '双人双锁', key: 'lock_required', render: (v) => v ? '🔒' : '—' }, { label: '库存', key: 'stock_qty', num: true, digits: 1 }, { label: '单位', key: 'stock_unit' },
                { label: '安全库存', key: 'safety_stock', num: true, digits: 1 },
            ],
            rows.map((r) => ({ ...r, _danger: r.stock_qty < r.safety_stock }))
        );
    document.getElementById('hc-submit').onclick = async () => {
        try {
            const res = await post('/hazchem/issue', { chemical_code: document.getElementById('hc-code').value, qty: Number(document.getElementById('hc-qty').value), dual_custody_confirmed: document.getElementById('hc-dual').checked });
            U.toast('领用成功 ' + res.name);
            window.RENDERERS.hazardous_chemical(main);
        } catch (e) { U.toast(e.message, 'error'); }
    };
};

// ============ 能耗 ============
window.RENDERERS.energy = async function (main) {
    const rows = await safeFetch(main, '/energy/latest');
    if (!rows) return;
    main.innerHTML = U.pageHeader('能耗管理', '<button class="btn" onclick="window.window.RENDERERS.energy(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.renderTable(
            [
                { label: '表计编号', key: 'code' }, { label: '名称', key: 'name' }, { label: '能源', key: 'energy_type' }, { label: '层级', key: 'meter_level' },
                { label: '累计读数', key: 'cumulative_value', num: true, digits: 1 }, { label: '本期用量', key: 'period_consumption', num: true, digits: 1 },
                { label: '本期金额', key: 'period_amount', money: true }, { label: '单位', key: 'unit' },
            ],
            rows
        );
};

// ============ 设备维护工单 ============
window.RENDERERS.maintenance = async function (main) {
    const rows = await safeFetch(main, '/maintenance/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('设备维护工单', '<button class="btn" onclick="window.window.RENDERERS.maintenance(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        `<div class="card"><div class="card-header"><h3>新建工单</h3></div><div class="card-body">
            <div class="row" style="gap:12px; flex-wrap:wrap;">
                <label>设备 <input id="mt-equip" value="OBP-001" style="width:120px"></label>
                <label>类型 <select id="mt-type" style="width:120px"><option value="bm">故障检修</option><option value="cm">纠正性</option><option value="pm">预防性</option></select></label>
                <label>优先级 <select id="mt-pri" style="width:100px"><option>1</option><option>2</option><option value="3">紧急</option></select></label>
                <button class="btn btn-primary" id="mt-submit">🔧 新建</button>
            </div>
        </div></div>` +
        U.renderTable(
            [
                { label: '工单号', key: 'name' }, { label: '设备', key: 'equipment' }, { label: '类型', key: 'maintenance_type' }, { label: '优先级', key: 'priority', badge: true },
                { label: '状态', key: 'state', badge: true }, { label: '责任人', key: 'assignee' }, { label: '计划日期', key: 'planned_date' },
            ],
            rows.map((r) => ({ ...r, _danger: r.priority === '3' }))
        );
    document.getElementById('mt-submit').onclick = async () => {
        try {
            const res = await post('/maintenance/order', { equipment_code: document.getElementById('mt-equip').value, maintenance_type: document.getElementById('mt-type').value, priority: document.getElementById('mt-pri').value });
            U.toast('工单 ' + res.name + ' 已创建');
            window.RENDERERS.maintenance(main);
        } catch (e) { U.toast(e.message, 'error'); }
    };
};

// ============ 备品备件 ============
window.RENDERERS.spare_part = async function (main) {
    const rows = await safeFetch(main, '/spare_part/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('备品备件', '<button class="btn" onclick="window.window.RENDERERS.spare_part(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.renderTable(
            [
                { label: '编号', key: 'code' }, { label: '名称', key: 'name' }, { label: '类别', key: 'category' }, { label: '适用设备', key: 'equipment' },
                { label: '库存', key: 'stock_qty', num: true, digits: 0 }, { label: '安全库存', key: 'min_stock_qty', num: true, digits: 0 }, { label: '单位', key: 'unit' },
                { label: '供应商', key: 'supplier' }, { label: '状态', key: 'is_low_stock', render: (v) => v ? U.stateBadge('低库存', 'danger') : U.stateBadge('充足', 'success') },
            ],
            rows.map((r) => ({ ...r, _danger: r.is_low_stock }))
        );
};

// ============ 资质证书 ============
window.RENDERERS.certificate = async function (main) {
    const rows = await safeFetch(main, '/certificate/list');
    if (!rows) return;
    const expiring = rows.filter((r) => r.is_valid && r.days_to_expire <= 30).length;
    const expired = rows.filter((r) => !r.is_valid).length;
    main.innerHTML = U.pageHeader('员工资质证书', '<button class="btn" onclick="window.window.RENDERERS.certificate(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.kpiCards([
            { label: '持证有效', value: rows.filter((r) => r.is_valid).length, sub: '有效证书', success: true },
            { label: '即将到期', value: expiring, sub: '30 天内', danger: expiring > 0 },
            { label: '已过期', value: expired, sub: '自动停工', danger: expired > 0 },
        ]) +
        U.renderTable(
            [
                { label: '证书', key: 'name' }, { label: '编号', key: 'cert_no' }, { label: '类型', key: 'cert_type' }, { label: '等级', key: 'cert_level' },
                { label: '持证人', key: 'holder' }, { label: '到期日期', key: 'expiry_date' }, { label: '距到期(天)', key: 'days_to_expire', num: true, digits: 0 },
                { label: '状态', key: 'is_valid', render: (v) => v ? U.stateBadge('有效', 'success') : U.stateBadge('已过期', 'danger') },
            ],
            rows.map((r) => ({ ...r, _danger: !r.is_valid || (r.is_valid && r.days_to_expire <= 30) }))
        );
};

// ============ 考勤 / 工时 ============
window.RENDERERS.attendance = async function (main) {
    const rows = await safeFetch(main, '/attendance/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('考勤 / 工时', '<button class="btn" onclick="window.window.RENDERERS.attendance(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.renderTable(
            [
                { label: '员工', key: 'employee' }, { label: '班次', key: 'shift_type' }, { label: '工位', key: 'workstation' },
                { label: '上班', key: 'check_in' }, { label: '下班', key: 'check_out' }, { label: '工时 (h)', key: 'work_hours', num: true, digits: 1 },
                { label: '报工数', key: 'report_count', num: true, digits: 0 }, { label: '产出 (g)', key: 'output_weight_g', num: true, digits: 3 },
                { label: '状态', key: 'attendance_state', badge: true },
            ],
            rows.map((r) => ({ ...r, _danger: r.attendance_state === 'absent' || r.attendance_state === 'late' }))
        );
};

// ============ SOP ============
window.RENDERERS.sop = async function (main) {
    const rows = await safeFetch(main, '/sop/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('SOP 作业指导书', '<button class="btn" onclick="window.window.RENDERERS.sop(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.renderTable(
            [
                { label: '编号', key: 'code' }, { label: '名称', key: 'name' }, { label: '关联工序', key: 'operation' }, { label: '版本', key: 'version' },
                { label: '类型', key: 'document_type' }, { label: '状态', key: 'state', badge: true }, { label: '生效日期', key: 'effective_date', render: (v) => v || '—' },
                { label: '编写人', key: 'author' },
            ],
            rows
        );
};

// ============ ECN ============
window.RENDERERS.ecn = async function (main) {
    const rows = await safeFetch(main, '/ecn/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('工程变更单 (ECN)', '<button class="btn" onclick="window.window.RENDERERS.ecn(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.renderTable(
            [
                { label: '变更单号', key: 'name' }, { label: '标题', key: 'title' }, { label: '类型', key: 'change_type' }, { label: '状态', key: 'state', badge: true },
                { label: '关联路线', key: 'route', render: (v) => v || '—' }, { label: '关联 BOM', key: 'bom', render: (v) => v || '—' },
                { label: '提出人', key: 'proposed_by' }, { label: '批准人', key: 'approved_by', render: (v) => v || '—' }, { label: '生效日期', key: 'effective_date', render: (v) => v || '—' },
            ],
            rows
        );
};
