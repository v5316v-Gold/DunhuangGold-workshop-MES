// 敦煌金 MES - 页面动态渲染器
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
    // 骨架屏 - 加载期间
    main.innerHTML = U.pageHeader('车间看板') +
        U.kpiCards([
            { label: '当日完工', value: '<span class="skeleton skeleton-line" style="height:32px;width:80px"></span>', sub: '加载中...' },
            { label: '进行中', value: '<span class="skeleton skeleton-line" style="height:32px;width:60px"></span>', sub: '加载中...' },
            { label: '超耗预警', value: '<span class="skeleton skeleton-line" style="height:32px;width:40px"></span>', sub: '加载中...' },
            { label: '当前金价', value: '<span class="skeleton skeleton-line" style="height:32px;width:120px"></span>', sub: '加载中...' },
        ]);
    const k = await safeFetch(main, '/dashboard/kpi');
    if (!k) return;

    // 注入渲染骨架,数字留空待 countUp
    main.innerHTML = U.pageHeader('车间看板',
        '<button class="btn btn-ripple" onclick="window.beautify.delay(200).then(()=>window.RENDERERS.dashboard(document.querySelector(\'.main\')))">🔄 刷新</button>'
        ) +
        U.kpiCards([
            {
                label: '当日完工',
                value: `<span class="big-number" data-count="${k.done_today}">0</span>`,
                sub: '件级 SN 已入库',
                success: true,
            },
            {
                label: '进行中',
                value: `<span class="big-number" data-count="${k.in_progress}">0</span>`,
                sub: '生产订单',
            },
            {
                label: '超耗预警',
                value: `<span class="big-number" data-count="${k.over_loss_count}">0</span>`,
                sub: k.over_loss_count > 0 ? '需复盘' : '今日正常',
                danger: k.over_loss_count > 0,
            },
            {
                label: '当前金价',
                value: `<span class="big-number gold" data-count="${k.current_gold_price}" data-decimals="2">0</span><span class="unit">/g</span>`,
                sub: 'Au9999 · SGE',
                gold: true,
            },
        ]) +
        U.kpiCards([
            {
                label: '库存估值',
                value: `<span class="big-number gold" data-count="${k.total_value}" data-decimals="0">¥0</span>`,
                sub: '按当前金价',
            },
            {
                label: '平均损耗率',
                value: `<span class="big-number" data-count="${k.avg_loss_rate}" data-decimals="2">0</span><span class="unit">%</span>`,
                sub: '今日',
            },
            {
                label: 'XRF 合格率',
                value: `<span class="big-number" data-count="${k.xrf_passed_pct}" data-decimals="1">0</span><span class="unit">%</span>`,
                sub: `${k.xrf_count_today} 次检测`,
            },
            {
                label: '油压 / 失蜡',
                value: `<span class="big-number" data-count="${k.oil_press_orders + k.lost_wax_orders}">0</span><span class="unit">单</span>`,
                sub: `油压 ${k.oil_press_orders} / 失蜡 ${k.lost_wax_orders}`,
            },
        ]) +
        `<div class="card card-glow" style="margin-top:16px"><div class="card-body">
            <div class="flex gap-3" style="align-items:center;flex-wrap:wrap">
                <span class="status-badge ${k.over_loss_count > 0 ? 'warning' : 'success'}">
                    ${k.over_loss_count > 0 ? '需关注' : '一切正常'}
                </span>
                <span class="text-secondary">📊 数据来自 <code>/api/v1/dashboard/kpi</code>(实时聚合)</span>
                <span class="text-muted hide-mobile">点击左侧菜单切换模块</span>
                <span class="text-muted" style="margin-left:auto">⌨ 按 <kbd class="kbd-hint">Ctrl+K</kbd> 打开命令面板</span>
            </div>
        </div></div>`;

    // 触发数字滚动动画(框架注入完后再启动)
    setTimeout(() => window.UI && window.UI.autoCountUp(), 80);
};

// 损耗监控预警(Phase 3.2 增强)
// 损耗监控预警 v3: 过滤 + 强卡片
window.RENDERERS.loss_monitor = async function (main) {
    main.innerHTML = U.pageHeader('📉 损耗监控预警', '<button class="btn btn-ripple" onclick="window.RENDERERS.loss_monitor(document.querySelector(' + "'" + '.main' + "'" + '))">🔄 刷新</button>') + '<div id="loss-monitor-content">' + U.loadingHTML('加载损耗数据...') + '</div>';
    const [alertsRaw, dash] = await Promise.all([
        safeFetch(main, '/loss/alerts'),
        safeFetch(main, '/loss/dashboard'),
    ]);
    if (!alertsRaw || !dash) return;
    const d = dash || {};
    const sevF = document.getElementById('loss-filter-severity')?.value || '';
    const statusF = document.getElementById('loss-filter-status')?.value || '';
    const searchK = document.getElementById('loss-search')?.value.toLowerCase().trim() || '';
    let alerts = alertsRaw;
    if (sevF) alerts = alerts.filter(a => a.severity === sevF);
    if (statusF) alerts = alerts.filter(a => a.status === statusF);
    if (searchK) alerts = alerts.filter(a => (a.name + ' ' + (a.description||'')).toLowerCase().includes(searchK));

    const severityLabel = { info: 'ℹ️ 提示', warning: '🟡 黄色', danger: '🔴 红色' };
    const typeLabel = { operation: '工序级', cumulative: '累积级', trend: '趋势级' };
    const statusBadge = { open: '⏳ 待处理', acknowledged: '👀 已确认', resolved: '✅ 已解决', ignored: '🚫 已忽略' };
    const iconMap = { info: 'ℹ️', warning: '⚠️', danger: '🔴' };

    const layerStats = '<div class="kpi-cards stagger-in" style="margin-bottom:16px">' +
        '<div class="kpi-card danger"><div class="label">待处理</div><div class="value">' + (d.open_count || 0) + '</div><div class="sub">需立即处置</div></div>' +
        '<div class="kpi-card warning"><div class="label">已确认</div><div class="value">' + (d.acknowledged_count || 0) + '</div><div class="sub">处置中</div></div>' +
        '<div class="kpi-card success"><div class="label">已解决</div><div class="value">' + (d.resolved_count || 0) + '</div><div class="sub">本周期</div></div>' +
        '<div class="kpi-card"><div class="label">工序级</div><div class="value">' + ((d.by_type && d.by_type.operation) || 0) + '</div><div class="sub">Layer 1</div></div>' +
        '<div class="kpi-card"><div class="label">累积级</div><div class="value">' + ((d.by_type && d.by_type.cumulative) || 0) + '</div><div class="sub">Layer 2</div></div>' +
        '<div class="kpi-card gold"><div class="label">趋势级</div><div class="value">' + ((d.by_type && d.by_type.trend) || 0) + '</div><div class="sub">Layer 3</div></div>' +
    '</div>';

    const ackFn = "window.apiPost('/loss/alerts/acknowledge', {alert_id:ID}).then(r=>{window.toast('success', '✓ ' + r.data.name); window.RENDERERS.loss_monitor(document.querySelector('.main'));})";
    const resolveFn = "resolveAlert(ID)";

    const alertCards = alerts.length === 0
        ? '<div class="alert-empty"><div class="alert-empty-icon">✅</div><div>暂无符合筛选条件的预警</div></div>'
        : alerts.map(a => {
            const isPending = a.status === 'open';
            const sevCls = a.severity || 'info';
            return '<div class="alert-card severity-' + sevCls + ' status-' + a.status + '">' +
                '<div class="alert-card-icon">' + (iconMap[sevCls] || '⚠️') + '</div>' +
                '<div class="alert-card-body">' +
                    '<div class="alert-card-title">' +
                        '<span class="alert-card-name">' + escapeHtml(a.name) + '</span>' +
                        '<span class="alert-card-badge severity-' + sevCls + '">' + (severityLabel[sevCls] || sevCls) + '</span>' +
                        '<span class="alert-card-type">' + (typeLabel[a.alert_type] || a.alert_type) + '</span>' +
                        '<span class="text-muted" style="font-size:11px;margin-left:auto">' + (statusBadge[a.status] || a.status) + '</span>' +
                    '</div>' +
                    '<div class="alert-card-desc">' + escapeHtml(a.description || '') + '</div>' +
                    '<div class="alert-card-meta">' +
                        (a.operation_id ? '<span>📍 ' + escapeHtml(a.operation_id) + '</span>' : '') +
                        (a.operator_id ? '<span>👤 ' + escapeHtml(a.operator_id) + '</span>' : '') +
                        (a.equipment_id ? '<span>🔧 ' + escapeHtml(a.equipment_id) + '</span>' : '') +
                        (a.z_score ? '<span>📊 Z=' + a.z_score.toFixed(2) + '</span>' : '') +
                        '<span>⏰ ' + a.triggered_at + '</span>' +
                    '</div>' +
                    (a.suggestion ? '<div class="alert-card-suggestion">💡 ' + escapeHtml(a.suggestion) + '</div>' : '') +
                '</div>' +
                (isPending ? '<div class="alert-card-actions">' +
                    '<button class="btn btn-ripple" onclick="' + ackFn.replace('ID', a.id) + '">👀 确认</button>' +
                    '<button class="btn btn-primary btn-ripple" onclick="' + resolveFn.replace('ID', a.id) + '">✓ 解决</button>' +
                '</div>' : '') +
            '</div>';
        }).join('');

    const html = layerStats + '<div class="alert-section-header">' +
        '<span class="alert-section-title">🔍 预警列表</span>' +
        '<span class="alert-section-count">' + alerts.length + ' / ' + alertsRaw.length + ' 条</span>' +
    '</div>' + alertCards;

    const el = main.querySelector('#loss-monitor-content');
    if (el) el.innerHTML = html;
};

function resolveAlert(alertId) {
    const note = prompt('解决说明(可选):', '');
    if (note === null) return;
    window.apiPost('/loss/alerts/resolve', { alert_id: alertId, note })
        .then(r => { window.toast('success', '✓ 已解决 ' + r.data.name); window.RENDERERS.loss_monitor(document.querySelector('.main')); });
}


function resolveAlert(alertId) {
    const note = prompt('解决说明(可选):', '');
    if (note === null) return;
    window.apiPost('/loss/alerts/resolve', { alert_id: alertId, note })
        .then(r => { window.toast('success', '✓ 已解决 ' + r.data.name); window.RENDERERS.loss_monitor(document.querySelector('.main')); });
}

// ============ 金料批次 ============
window.RENDERERS.material_batch = async function (main) {
    main.innerHTML = U.pageHeader('金料批次') + U.kpiCards([
        { label: '可用库存', value: '<span class="skeleton skeleton-line" style="height:32px;width:120px"></span>', sub: '加载中...' },
        { label: '批次总数', value: '<span class="skeleton skeleton-line" style="height:32px;width:50px"></span>', sub: '加载中...' },
    ]);
    const rows = await safeFetch(main, '/batch/list');
    if (!rows) return;
    const totalNet = rows.reduce((s, r) => s + r.net_weight_g, 0);
    const totalAvail = rows.reduce((s, r) => s + r.available_weight_g, 0);
    const totalValue = rows.reduce((s, r) => s + r.current_value, 0);

    // 空状态:无批次数据
    if (!rows.length) {
        main.innerHTML = U.pageHeader('金料批次') +
            U.emptyStateHTML({
                icon: '💰',
                title: '暂无金料批次',
                desc: '金库空空如也,请先入库金料或等待供应商来料',
                actionLabel: '新建批次',
                actionOnClick: 'window.toast && window.toast("info", "功能建设中")',
            });
        return;
    }

    main.innerHTML = U.pageHeader('金料批次', '<button class="btn btn-ripple" onclick="window.RENDERERS.material_batch(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.kpiCards([
            { label: '可用库存', value: `<span class="big-number" data-count="${totalAvail}" data-decimals="3">0</span><span class="unit">g</span>`, sub: '¥ ' + U.num(totalValue, 0), gold: true },
            { label: '批次总数', value: `<span class="big-number" data-count="${rows.length}">0</span>`, sub: '精度 0.001g' },
            { label: '待检验', value: `<span class="big-number" data-count="${rows.filter(r => r.inspection_state === 'pending').length}">0</span>`, sub: '100% 已检', success: true },
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
    setTimeout(() => window.UI && window.UI.autoCountUp(), 80);
};

// 损耗监控预警(Phase 3.2 增强)
function resolveAlert(alertId) {
    const note = prompt('解决说明(可选):', '');
    if (note === null) return;
    window.apiPost('/loss/alerts/resolve', { alert_id: alertId, note })
        .then(r => { window.toast('success', '✓ 已解决 ' + r.data.name); window.RENDERERS.loss_monitor(document.querySelector('.main')); });
}

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

// ============ Phase 3: 车间作业全流程 ============

// 任务单接收列表
window.RENDERERS.production_list = async function (main) {
    const rows = await safeFetch(main, '/production/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('📥 任务单接收', '<button class="btn btn-ripple" onclick="window.RENDERERS.production_list(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        '<div class="stagger-in">' +
        rows.map(r => {
            const stateBadge = U.statusBadgeHTML(r.gold_state, ({received:'已接收',in_progress:'进行中',done:'已完成',cancelled:'已取消'})[r.gold_state] || r.gold_state);
            return `
            <div class="card" style="margin-bottom:12px">
                <div class="card-body flex gap-3" style="align-items:center">
                    <div style="flex:1">
                        <div class="flex gap-2" style="align-items:center;margin-bottom:4px">
                            <span class="text-bold text-gold" style="font-size:18px">${r.name}</span>
                            ${stateBadge}
                            <span class="text-muted">·</span>
                            <span class="text-secondary">${r.process_type === 'oil_press' ? '油压' : '失蜡'}</span>
                        </div>
                        <div class="text-secondary">${r.product} × ${r.qty} 件</div>
                        <div class="text-muted" style="font-size:12px;margin-top:4px">
                            接收: ${r.received_at || '—'} · 当前工位: ${r.current_workstation || '—'}
                        </div>
                    </div>
                    ${r.gold_state === 'received' ? `<button class="btn btn-primary btn-ripple" onclick="window.apiPost('/production/receive', {production_id:${r.id}, note:'班组长已确认材料'}).then(()=>{window.toast('success','已开工'); window.RENDERERS.production_list(document.querySelector('.main'))})">▶ 开工</button>` : `<span class="text-muted">${r.gold_state === 'done' ? '✓ 完成' : '⏵ 进行中'}</span>`}
                </div>
            </div>
        `}).join('') + '</div>';
};

// 工序交接卡列表
window.RENDERERS.flow_card = async function (main) {
    const rows = await safeFetch(main, '/flow_card/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('🔄 工序交接卡', '<button class="btn btn-ripple" onclick="window.RENDERERS.flow_card(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.renderTable([
            { label: '交接卡号', key: 'name' },
            { label: '件级 SN', key: 'sn' },
            { label: '接收工序', key: 'in_operation' },
            { label: '接收工位', key: 'in_workstation' },
            { label: '发送人', key: 'sender' },
            { label: '接收人', key: 'receiver' },
            { label: '交接时间', key: 'handover_time' },
            { label: '状态', key: 'state', badge: true },
        ], rows);
};

// 件级追溯查询
window.RENDERERS.piece_trace = async function (main, sn) {
    sn = sn || 'GLD-20260805-RING-001';
    main.innerHTML = `<div class="loading-state"><div class="spinner-gold"></div><div class="loading-text">追溯 SN ${sn}...</div></div>`;
    const data = await safeFetch(main, `/piece/trace?sn=${encodeURIComponent(sn)}`);
    if (!data || !data.found) {
        main.innerHTML = U.emptyStateHTML({ icon: '🔍', title: 'SN 不存在', desc: `未找到 SN ${sn} 的记录`, actionLabel: '重试', actionOnClick: `document.getElementById('trace-sn').focus()` });
        return;
    }
    main.innerHTML = U.pageHeader('🔖 件级追溯: ' + data.sn) + `
        <div class="card card-glow" style="margin-bottom:16px">
            <div class="card-body">
                <div class="flex gap-4" style="align-items:center;flex-wrap:wrap">
                    <div>
                        <div class="text-muted" style="font-size:12px">件级 SN</div>
                        <div class="text-gold text-bold" style="font-size:20px">${data.sn}</div>
                    </div>
                    <div>
                        <div class="text-muted" style="font-size:12px">产品</div>
                        <div>${data.product}</div>
                    </div>
                    <div>
                        <div class="text-muted" style="font-size:12px">当前状态</div>
                        <div>${U.statusBadgeHTML(data.current_state, data.current_state)}</div>
                    </div>
                    <div>
                        <div class="text-muted" style="font-size:12px">当前工位</div>
                        <div>${data.current_workstation || '—'}</div>
                    </div>
                    <div>
                        <div class="text-muted" style="font-size:12px">当前工序</div>
                        <div>${data.current_operation || '—'}</div>
                    </div>
                </div>
            </div>
        </div>
        <h3 style="margin:16px 0 8px">🛤 完整旅程 (${data.flow_cards.length} 道交接)</h3>
        <div class="stagger-in">
            ${data.flow_cards.map((c, i) => `
                <div class="trace-step ${c.state}">
                    <div class="step-num">${i + 1}</div>
                    <div class="step-content">
                        <div class="step-title">${c.out_operation || '(首道)'} → ${c.in_operation}</div>
                        <div class="step-meta">${c.handover_time} · ${c.in_workstation} · ${c.sender} → ${c.receiver || '待接收'}</div>
                        <div class="step-stats">
                            <span><span class="stat-label">进入:</span> <span class="stat-value">${c.weight_in_g}g</span></span>
                            <span><span class="stat-label">发出:</span> <span class="stat-value">${c.weight_out_g || '—'}g</span></span>
                            <span><span class="stat-label">本工序损耗:</span> <span class="stat-value">${c.weight_loss_g}g</span></span>
                            <span><span class="stat-label">状态:</span> ${U.statusBadgeHTML(c.state, c.state)}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
};

// NCR 不合格品处理
window.RENDERERS.ncr = async function (main) {
    const [ncrs, dash] = await Promise.all([
        safeFetch(main, '/ncr/list'),
        safeFetch(main, '/ncr/dashboard'),
    ]);
    if (!ncrs) return;
    const d = dash.data || {};
    main.innerHTML = U.pageHeader('⚠ NCR 不合格品处理', '<button class="btn btn-ripple" onclick="window.RENDERERS.ncr(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        U.kpiCards([
            { label: '7天 NCR', value: d.total_7days || 0, sub: '本周期', success: true },
            { label: '待处置', value: d.pending || 0, sub: '需立即处理', danger: d.pending > 0 },
            { label: '返工中', value: d.rework || 0, sub: '重做中' },
            { label: '报废', value: d.scrap || 0, sub: '已销毁', danger: d.scrap > 0 },
            { label: '让步放行', value: d.concession || 0, sub: '降级销售' },
            { label: '估计损失', value: '¥ ' + U.num(d.total_loss_amount || 0, 0), sub: '本周期', danger: d.total_loss_amount > 0 },
        ]) +
        U.renderTable([
            { label: 'NCR 编号', key: 'name' },
            { label: '发现时间', key: 'ncr_time' },
            { label: '来源', key: 'source' },
            { label: '缺陷类型', key: 'defect_type' },
            { label: '关联件 SN', key: 'piece_sn' },
            { label: '重量 (g)', key: 'defect_weight_g', num: true, digits: 3 },
            { label: '处置', key: 'disposition', render: (v) => `<span class="ncr-disp ${v}">${({pending:'待处置',rework:'返工',concession:'让步',scrap:'报废',closed:'已关'})[v] || v}</span>` },
            { label: '处置人', key: 'disposition_by' },
            { label: '估计损失', key: 'estimated_loss_amount', num: true, digits: 0, render: (v) => '¥ ' + U.num(v || 0, 0) },
        ], ncrs);
};

// 包装
window.RENDERERS.package = async function (main) {
    const rows = await safeFetch(main, '/package/list');
    if (!rows) return;
    main.innerHTML = U.pageHeader('📦 包装', '<button class="btn btn-ripple" onclick="window.RENDERERS.package(document.querySelector(\'.main\'))">🔄 刷新</button>') +
        rows.map(r => `
        <div class="pkg-card">
            <div style="flex:1">
                <div class="pkg-no">📦 ${r.name}</div>
                <div class="pkg-meta">${r.package_kind === 'box' ? '盒装' : '箱装'} · ${r.production_name || '—'} · ${r.package_time}</div>
                <div class="pkg-cert">🛡 NGTC 证书号: ${r.ngtc_cert_no || '—'}</div>
                <div class="pkg-stats">
                    <div><div class="stat-label">件数</div><div class="stat-value">${r.piece_count}</div></div>
                    <div><div class="stat-label">总重量</div><div class="stat-value">${U.num(r.total_weight_g, 1)}g</div></div>
                    <div><div class="stat-label">总价值</div><div class="stat-value">¥ ${U.num(r.total_value, 0)}</div></div>
                    <div><div class="stat-label">封箱时间</div><div class="stat-value" style="font-size:14px">${r.sealed_time || '—'}</div></div>
                </div>
            </div>
            <div style="text-align:right">
                ${U.statusBadgeHTML(r.state, ({draft:'草稿',sealed:'已封箱',stored:'已入库',shipped:'已发货',opened:'已拆封'})[r.state] || r.state)}
            </div>
        </div>
    `).join('');
};

// 车间大屏 (Phase 3 核心)
window.RENDERERS.bigscreen = async function (main) {
    const d = await safeFetch(main, '/workshop/bigscreen');
    if (!d || !d.summary) {
        main.innerHTML = U.emptyStateHTML({ icon: '🖥️', title: '大屏数据加载失败', desc: '请检查网络或刷新重试', actionLabel: '重试', actionOnClick: 'window.RENDERERS.bigscreen(document.querySelector(\'.main\'))' });
        return;
    }
    const s = d.summary;
    const ops = d.operations;
    const bns = d.bottlenecks;
    const lt = d.loss_trend;

    main.innerHTML = U.pageHeader('🖥️ 车间大屏 (65寸实时)', '<button class="btn btn-ripple" onclick="window.RENDERERS.bigscreen(document.querySelector(\'.main\'))">🔄 刷新</button>') + `
        <div class="bigscreen-top stagger-in">
            <div class="kpi-card success"><div class="label">今日完工</div><div class="value" data-count="${s.done_today}">${s.done_today}</div></div>
            <div class="kpi-card"><div class="label">进行中</div><div class="value" data-count="${s.in_progress}">${s.in_progress}</div></div>
            <div class="kpi-card warning"><div class="label">待接收</div><div class="value" data-count="${s.pending_receive}">${s.pending_receive}</div></div>
            <div class="kpi-card danger"><div class="label">超耗预警</div><div class="value" data-count="${s.over_loss_alerts}">${s.over_loss_alerts}</div></div>
            <div class="kpi-card danger"><div class="label">NCR 待处置</div><div class="value" data-count="${s.ncr_pending}">${s.ncr_pending}</div></div>
            <div class="kpi-card success"><div class="label">今日包装</div><div class="value" data-count="${s.packages_today}">${s.packages_today}</div></div>
            <div class="kpi-card gold"><div class="label">平均损耗率</div><div class="value" data-count="${s.avg_loss_rate}" data-decimals="2">${s.avg_loss_rate.toFixed(1)}<span class="unit">%</span></div></div>
        </div>
        <div class="card card-glow" style="margin-top:16px">
            <div class="card-header"><h3>🔧 9 道工序实时状态</h3></div>
            <div class="card-body">
                <div class="operations-strip stagger-in">
                    ${ops.map(op => {
                        const stateEmoji = {running:'🟢',idle:'⚪',warning:'🟡',danger:'🔴'}[op.state] || '⚪';
                        return `<div class="op-block ${op.state}">
                            <div class="op-name">${op.name}</div>
                            <div class="op-state">${stateEmoji}</div>
                            <div class="op-queue">积压 ${op.queue}</div>
                        </div>`;
                    }).join('')}
                </div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px">
            <div class="card card-glow">
                <div class="card-header"><h3>📈 5 天损耗趋势</h3></div>
                <div class="card-body">
                    <div class="loss-bars">
                        ${lt.map((d, i) => {
                            const heightPct = Math.max(20, Math.min(100, d.avg_loss_rate * 20));
                            return `<div class="loss-bar" style="height:${heightPct}%">
                                <div class="value">${d.avg_loss_rate}%</div>
                                <div class="label">${d.date.slice(5)}</div>
                            </div>`;
                        }).join('')}
                    </div>
                </div>
            </div>
            <div class="card card-glow">
                <div class="card-header"><h3>🐌 瓶颈工位 TOP 3</h3></div>
                <div class="card-body">
                    ${bns.map((b, i) => `<div class="bn-row">
                        <div class="bn-rank">#${i + 1}</div>
                        <div class="bn-info">
                            <div class="text-bold">${b.workstation}</div>
                            <div class="text-muted" style="font-size:12px">积压 ${b.queue_count} 件</div>
                        </div>
                        <div class="bn-stats">
                            <div>平均等待</div>
                            <div class="wait">${b.avg_wait_min} 分钟</div>
                        </div>
                    </div>`).join('')}
                </div>
            </div>
        </div>
        <div class="card" style="margin-top:16px;background:linear-gradient(90deg,var(--error-bg) 0%,transparent 100%)">
            <div class="card-body">
                <span class="text-danger text-bold">⚠ 实时报警:</span>
                <span class="text-secondary" style="margin-left:12px">
                    [10:35] NCR-20260805-0001 执模工序划痕,已返工
                    &nbsp;&nbsp; [11:15] NCR-20260805-0002 XRF 含量 99.42% 不达标,班组长处置中
                </span>
            </div>
        </div>
    `;
    setTimeout(() => window.UI && window.UI.autoCountUp(), 80);
};

// 损耗监控预警(Phase 3.2 增强)
function resolveAlert(alertId) {
    const note = prompt('解决说明(可选):', '');
    if (note === null) return;
    window.apiPost('/loss/alerts/resolve', { alert_id: alertId, note })
        .then(r => { window.toast('success', '✓ 已解决 ' + r.data.name); window.RENDERERS.loss_monitor(document.querySelector('.main')); });
}
