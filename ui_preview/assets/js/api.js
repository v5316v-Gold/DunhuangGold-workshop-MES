// 敦煌金 ERP - API 封装 + 通用渲染辅助
// 数据来自本机 mock API (/api/v1/*)，结构对齐 Odoo REST 契约

const API_BASE = '/api/v1';

async function apiGet(path) {
    const resp = await fetch(API_BASE + path);
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || '请求失败');
    return data.data;
}

async function apiPost(path, body) {
    const resp = await fetch(API_BASE + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}),
    });
    const data = await resp.json();
    if (!data.ok) throw new Error(data.error || '请求失败');
    return data.data;
}

// ---------- 通用渲染辅助 ----------
function escapeHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function badge(text, type) {
    const cls = type ? `badge badge-${type}` : 'badge';
    return `<span class="${cls}">${escapeHtml(text)}</span>`;
}

// 状态徽章映射 (中文状态 → badge 类型)
function stateBadge(state, map) {
    const m = map || {
        'draft': 'info', '草稿': 'info',
        'available': 'success', '可用': 'success', 'confirmed': 'success', '已确认': 'success', 'posted': 'success', '已过账': 'success', '已入库': 'success', 'done': 'success', '已回库': 'success',
        'running': 'success', '运行': 'success', 'normal': 'success', '正常': 'success', 'passed': 'success', '合格': 'success', '已生效': 'success', 'effective': 'success',
        'in_progress': 'warning', '进行中': 'warning', 'counting': 'warning', '盘点中': 'warning', 'review': 'warning', '评审中': 'warning', 'planned': 'info', '已计划': 'info',
        'maintenance': 'warning', '保养': 'warning', 'late': 'warning', '迟到': 'warning', 'approved': 'info', '已批准': 'info',
        'down': 'danger', '故障': 'danger', 'alarm': 'danger', '超限报警': 'danger', 'failed': 'danger', '不合格': 'danger', 'depleted': 'muted', '已耗尽': 'muted', 'scrap': 'danger', '报废': 'danger', '盘亏': 'danger', '缺勤': 'danger', 'absent': 'danger', '已过期': 'danger', '低库存': 'danger',
        'rework': 'warning', '返工': 'warning', 'cancelled': 'muted', '已取消': 'muted', '已作废': 'muted', 'obsolete': 'muted',
    };
    return badge(state, m[state] || '');
}

function num(v, digits) {
    if (v == null || v === '—' || v === '') return '—';
    const n = Number(v);
    if (isNaN(n)) return escapeHtml(v);
    return n.toLocaleString('zh-CN', { minimumFractionDigits: digits || 2, maximumFractionDigits: digits || 2 });
}

function money(v) {
    if (v == null) return '—';
    return '¥ ' + Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// 渲染 KPI 卡片
function kpiCards(cards) {
    return `<div class="kpi-grid">${cards.map((c) => {
        const style = c.danger ? 'style="border-left-color: var(--danger);"' : (c.gold ? 'class="kpi-card gold"' : (c.success ? 'class="kpi-card success"' : 'class="kpi-card"'));
        return `<div ${style === 'class="kpi-card gold"' || style === 'class="kpi-card success"' ? style : 'class="kpi-card"'}>
            <div class="label">${escapeHtml(c.label)}</div>
            <div class="value" ${c.danger ? 'style="color: var(--danger);"' : (c.gold ? 'class="gold"' : '')}>${c.value}</div>
            ${c.sub ? `<div class="sub">${escapeHtml(c.sub)}</div>` : ''}
        </div>`;
    }).join('')}</div>`;
}

// 渲染表格 (行状态优先级: danger > warning > success > info > gold)
function renderTable(columns, rows, foot) {
    const head = `<tr>${columns.map((c) => `<th class="${c.cls || ''}">${escapeHtml(c.label)}</th>`).join('')}</tr>`;
    const body = rows.map((row) => {
        // 行状态: _danger / _warning / _success / _info / _gold (按优先级)
        let rowCls = '';
        if (row._danger) rowCls = 'row-danger';
        else if (row._warning) rowCls = 'row-warning';
        else if (row._success) rowCls = 'row-success';
        else if (row._gold) rowCls = 'row-gold';
        else if (row._info) rowCls = 'row-info';

        const tds = columns.map((c) => {
            let val = row[c.key];
            if (c.render) val = c.render(row[c.key], row);
            else if (c.num) val = `<span class="number">${num(row[c.key], c.digits)}</span>`;
            else if (c.money) val = `<span class="number currency">${money(row[c.key])}</span>`;
            else if (c.badge) val = stateBadge(row[c.key], c.badgeMap);
            else val = escapeHtml(row[c.key]);
            return `<td class="${c.cls || ''}">${val}</td>`;
        }).join('');
        return `<tr class="${rowCls}">${tds}</tr>`;
    }).join('');
    const footHtml = foot ? `<tfoot><tr class="tfoot-row" style="font-weight: 600;">${foot}</tr></tfoot>` : '';
    return `<div class="card"><div class="card-body dense"><table class="data"><thead>${head}</thead><tbody>${body}</tbody>${footHtml}</table></div></div>`;
}

// 页面骨架
function pageHeader(title, actions) {
    return `<div class="page-header"><h1>${escapeHtml(title)}</h1><div class="actions">${actions || ''}</div></div>`;
}

function notice(type, html) {
    return `<div class="notice ${type}">${html}</div>`;
}

function toast(msg, type) {
    let el = document.getElementById('app-toast');
    if (!el) {
        el = document.createElement('div');
        el.id = 'app-toast';
        el.className = 'toast-item animate-slide-in-right';
        el.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;padding:12px 20px;font-size:14px;transition:all 0.3s;';
        document.body.appendChild(el);
    }
    el.className = 'toast-item animate-slide-in-right ' + (type === 'error' ? 'toast-error' : 'toast-success');
    el.textContent = msg;
    el.style.opacity = '1';
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.style.opacity = '0'; }, 2500);
}

// 全局 API 与辅助挂到 window 供 renderer 使用
window.API = { get: apiGet, post: apiPost };
window.UI = { escapeHtml, badge, stateBadge, num, money, kpiCards, renderTable, pageHeader, notice, toast };
