// 伪 Odoo 17 — 敦煌金加工车间 ERP 离线预览
// 导航 + 页面切换 (Phase 3.2 优化: 9 sections 按业务流程分组)

const NAV = [
    {section: "工作台", items: [
        {id: "dashboard", name: "车间看板", icon: "📊", file: "page_dashboard.html", desc: "今日关键 KPI"},
        {id: "bigscreen", name: "车间大屏", icon: "🖥️", file: "page_bigscreen.html", desc: "65寸实时监控"},
        {id: "loss_monitor", name: "损耗监控预警", icon: "🚨", file: "page_loss_monitor.html", desc: "3 层监控 + Z-Score"},
    ]},
    {section: "任务执行", items: [
        {id: "production_list", name: "任务单接收", icon: "📥", file: "page_production_list.html", desc: "车间班组长接收"},
        {id: "workorder_report", name: "工序报工", icon: "📝", file: "page_workorder_report.html", desc: "称重直采报工"},
        {id: "flow_card", name: "工序交接卡", icon: "🔄", file: "page_flow_card.html", desc: "扫码交接记录"},
        {id: "piece_trace", name: "件级追溯", icon: "🔖", file: "page_piece_trace.html", desc: "SN 完整旅程"},
        {id: "outsource", name: "委外加工", icon: "🤝", file: "page_outsource.html", desc: "失蜡/镶石/电镀"},
    ]},
    {section: "质量管控", items: [
        {id: "qc", name: "质检记录", icon: "✅", file: "page_quality.html", desc: "件级质量判定"},
        {id: "xrf", name: "XRF 含量检测", icon: "🔬", file: "page_xrf.html", desc: "金/铂/钯含量"},
        {id: "imprint", name: "印记记录", icon: "📍", file: "page_imprint.html", desc: "GB 11887 三级分离"},
        {id: "ncr", name: "NCR 不合格品", icon: "⚠️", file: "page_ncr.html", desc: "返工/让步/报废"},
        {id: "loss_trace", name: "损耗追溯", icon: "📉", file: "page_loss_trace.html", desc: "工序损耗链"},
        {id: "piece", name: "件级 SN", icon: "🏷️", file: "page_piece.html", desc: "一物一码"},
    ]},
    {section: "入库包装", items: [
        {id: "finished_goods", name: "成品入库", icon: "📦", file: "page_finished_goods.html", desc: "SN 入库"},
        {id: "package", name: "包装", icon: "🎁", file: "page_package.html", desc: "盒装 + NGTC"},
        {id: "material_return", name: "班后回料", icon: "↩️", file: "page_material_return.html", desc: "浇口/边角料"},
    ]},
    {section: "金料管理", items: [
        {id: "material_batch", name: "金料批次", icon: "💰", file: "page_material_batch.html", desc: "0.001g 精度"},
        {id: "price_engine", name: "实时金价", icon: "📈", file: "page_price_engine.html", desc: "SGE/LBMA 推送"},
        {id: "recycle", name: "旧金回收", icon: "♻️", file: "page_recycle.html", desc: "客户实名 + XRF"},
        {id: "inventory_count", name: "金料盘点", icon: "🧮", file: "page_inventory_count.html", desc: "账实对比"},
    ]},
    {section: "设备", items: [
        {id: "equipment", name: "设备台账", icon: "⚙️", file: "page_equipment.html", desc: "OEE + 维护"},
        {id: "workstation", name: "工位", icon: "🔲", file: "page_workstation.html", desc: "工位排布"},
        {id: "maintenance", name: "设备维护", icon: "🛠️", file: "page_maintenance.html", desc: "PM/CM/BM"},
        {id: "spare_part", name: "备品备件", icon: "🔩", file: "page_spare_part.html", desc: "低库存预警"},
    ]},
    {section: "工艺", items: [
        {id: "process_operation", name: "工艺工序", icon: "🔧", file: "page_process_operation.html", desc: "油压 9 + 失蜡 11"},
        {id: "process_route", name: "工艺路线模板", icon: "🛤️", file: "page_process_route.html", desc: "OWP_STD / LWC_STD"},
        {id: "sop", name: "SOP 作业指导书", icon: "📄", file: "page_sop.html", desc: "标准操作"},
        {id: "ecn", name: "工程变更 ECN", icon: "🔄", file: "page_ecn.html", desc: "工艺变更审批"},
        {id: "measurement", name: "计量单位", icon: "⚖️", file: "page_measurement.html", desc: "克/钱/两/克拉"},
        {id: "mold", name: "模具台账", icon: "🔨", file: "page_mold.html", desc: "寿命 + 报废"},
        {id: "wax", name: "蜡模管理", icon: "🕯️", file: "page_wax_model.html", desc: "失蜡铸造"},
    ]},
    {section: "人员", items: [
        {id: "certificate", name: "员工资质证书", icon: "🎓", file: "page_certificate.html", desc: "熔金/镶石/抛光"},
        {id: "attendance", name: "考勤工时", icon: "🕒", file: "page_attendance.html", desc: "工时统计"},
    ]},
    {section: "安环", items: [
        {id: "environment", name: "环境监测", icon: "🌡️", file: "page_environment.html", desc: "温湿度/VOC"},
        {id: "hazardous_chemical", name: "危化品", icon: "⚠️", file: "page_hazardous_chemical.html", desc: "双人双锁"},
        {id: "energy", name: "能耗管理", icon: "⚡", file: "page_energy.html", desc: "水电气"},
    ]},
    {section: "预留", items: [
        {id: "procurement", name: "采购订单 (预留)", icon: "📦", file: "page_procurement.html"},
        {id: "sale", name: "销售订单 (预留)", icon: "🛒", file: "page_sale.html"},
    ]},
];

// 当前页
let currentPage = location.hash.slice(1) || "dashboard";

// 搜索关键词(全局)
let menuSearchKeyword = "";

// 最近访问(localStorage, 最多 5 条)
const RECENT_KEY = "gold_mes_recent_pages";
function getRecent() {
    try { return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]"); }
    catch (e) { return []; }
}
function pushRecent(pageId) {
    let arr = getRecent().filter(id => id !== pageId);
    arr.unshift(pageId);
    arr = arr.slice(0, 5);
    localStorage.setItem(RECENT_KEY, JSON.stringify(arr));
}

// 渲染菜单(支持搜索过滤 + 最近访问)
function renderMenu() {
    const sidebar = document.querySelector(".sidebar");
    if (!sidebar) return;
    const recent = getRecent();
    const keyword = menuSearchKeyword.toLowerCase().trim();

    // 搜索模式: 扁平展示所有匹配项
    if (keyword) {
        const matches = [];
        NAV.forEach(section => {
            section.items.forEach(item => {
                const haystack = `${item.name} ${item.id} ${item.desc || ''} ${section.section}`.toLowerCase();
                if (haystack.includes(keyword)) {
                    matches.push({ ...item, section: section.section });
                }
            });
        });
        if (!matches.length) {
            sidebar.innerHTML = `<div class="menu-empty">
                <div class="menu-empty-icon">🔍</div>
                <div class="menu-empty-text">没有匹配 "<b>${escapeHtml(keyword)}</b>"</div>
                <div class="menu-empty-hint">试试其他关键词</div>
            </div>`;
            return;
        }
        let html = `<div class="menu-section"><div class="menu-section-title">🔍 搜索结果 (${matches.length})</div>`;
        matches.forEach(item => {
            const active = item.id === currentPage ? "active" : "";
            html += renderMenuItem(item, active, item.section);
        });
        html += `</div>`;
        sidebar.innerHTML = html;
        return;
    }

    // 正常模式: 分组渲染
    let html = "";

    // 最近访问(如果非空)
    if (recent.length > 0) {
        html += `<div class="menu-section">`;
        html += `<div class="menu-section-title recent">⏱ 最近访问</div>`;
        recent.forEach(pageId => {
            const item = findPage(pageId);
            if (!item) return;
            const active = item.id === currentPage ? "active" : "";
            html += renderMenuItem(item, active, '最近');
        });
        html += `</div>`;
    }

    NAV.forEach(section => {
        // 计算该 section 有多少个匹配项(空搜索)
        html += `<div class="menu-section">`;
        html += `<div class="menu-section-title">${section.section} <span class="section-count">${section.items.length}</span></div>`;
        section.items.forEach(item => {
            const active = item.id === currentPage ? "active" : "";
            html += renderMenuItem(item, active, section.section);
        });
        html += `</div>`;
    });
    sidebar.innerHTML = html;
}

// 渲染单个菜单项(供搜索和正常模式共用)
function renderMenuItem(item, active, section) {
    const badgeHtml = getBadgeHtml(item.id);
    const descHtml = (item.desc && !active) ? `<span class="item-desc">${escapeHtml(item.desc)}</span>` : '';
    return `<a class="menu-item ${active}" href="#${item.id}" data-id="${item.id}" data-section="${escapeHtml(section)}" title="${escapeHtml(item.desc || item.name)}">
        <span class="icon">${item.icon}</span>
        <div class="item-main">
            <span class="item-name">${highlightKeyword(item.name, menuSearchKeyword)}</span>
            ${descHtml}
        </div>
        ${badgeHtml}
    </a>`;
}

// 关键词高亮
function highlightKeyword(text, keyword) {
    if (!keyword) return escapeHtml(text);
    const k = keyword.toLowerCase();
    const idx = text.toLowerCase().indexOf(k);
    if (idx < 0) return escapeHtml(text);
    return escapeHtml(text.slice(0, idx))
         + '<mark class="hl">' + escapeHtml(text.slice(idx, idx + k.length)) + '</mark>'
         + escapeHtml(text.slice(idx + k.length));
}

// 菜单徽章(待处理数量)
function getBadgeHtml(itemId) {
    const map = {
        'loss_monitor': { count: 4, type: 'danger' },  // 待处理预警
        'ncr': { count: 1, type: 'warning' },          // NCR 待处置
        'inventory_count': { count: 0, type: 'muted' },
    };
    const b = map[itemId];
    if (!b || b.count <= 0) return '';
    return `<span class="badge badge-${b.type}">${b.count}</span>`;
}

function escapeHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function navigate(pageId) {
    if (currentPage !== pageId) {
        currentPage = pageId;
        location.hash = pageId;
        pushRecent(pageId);
        renderMenu();
        updateBreadcrumb();
    }
    loadPage(pageId);
}

// 暴露给 shortcuts.js / 命令面板
window.navigate = navigate;
window.NAV = NAV;

function findPage(itemId) {
    for (const section of NAV) {
        const f = section.items.find(i => i.id === itemId);
        if (f) return f;
    }
    return NAV[NAV.length - 1].items[0];
}

function updateBreadcrumb() {
    const page = findPage(currentPage);
    if (!page) return;
    document.querySelector(".breadcrumb").innerHTML = `
        <a href="#dashboard">车间</a>
        <span> / </span>
        <span>${page.name}</span>
    `;
    document.title = `敦煌金加工车间 ERP - ${page.name}`;
}

async function loadPage(itemId) {
    const page = findPage(itemId);
    if (!page) return;
    const main = document.querySelector(".main");
    // 美化: 金色 spinner + 加载文案
    main.innerHTML = window.UI
        ? window.UI.loadingHTML(`正在加载 ${page.name}...`)
        : '<div class="notice info">🔄 加载中...</div>';
    try {
        const resp = await fetch(`pages/${page.file}`);
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        const html = await resp.text();
        main.innerHTML = html;
        // 动态渲染: 页面加载后调用对应 renderer
        if (window.RENDERERS && typeof window.RENDERERS[itemId] === 'function') {
            await window.RENDERERS[itemId](main);
        }
        // 美化: 渲染后自动滚动数字 + 应用交错入场动画
        setTimeout(() => {
            if (window.UI && window.UI.autoCountUp) window.UI.autoCountUp();
            // 给主区域加交错入场
            const cards = main.querySelectorAll('.kpi-cards, tbody, .menu-section');
            cards.forEach(c => c.classList.add('stagger-in'));
        }, 50);
    } catch (e) {
        main.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <div class="empty-state-title">加载失败</div>
                <div class="empty-state-desc">${e.message}<br>注意: 本预览需要通过 HTTP 服务器访问</div>
                <button class="btn btn-primary btn-ripple" onclick="location.reload()">重新加载</button>
            </div>
        `;
    }
}

function toggleSidebar() {
    document.querySelector(".sidebar").classList.toggle("collapsed");
    document.querySelector(".main").classList.toggle("full");
}

document.addEventListener("DOMContentLoaded", () => {
    // 不需要显式 renderMenu, navigate() 内部会调用
    updateBreadcrumb();
    // 绑定菜单点击
    document.querySelector(".sidebar").addEventListener("click", (e) => {
        const link = e.target.closest(".menu-item");
        if (link) {
            e.preventDefault();
            navigate(link.dataset.id);
        }
    });
    // 绑定顶栏菜单切换
    document.querySelector(".menu-toggle").addEventListener("click", toggleSidebar);
    // 绑定搜索框(实时过滤菜单)
    const searchInput = document.querySelector(".navbar .search");
    if (searchInput) {
        let searchTimer = null;
        searchInput.addEventListener("input", (e) => {
            clearTimeout(searchTimer);
            const v = e.target.value;
            searchTimer = setTimeout(() => {
                menuSearchKeyword = v;
                renderMenu();
            }, 100);
        });
        searchInput.addEventListener("keydown", (e) => {
            if (e.key === 'Escape') {
                e.target.value = '';
                menuSearchKeyword = '';
                renderMenu();
                e.target.blur();
            }
        });
    }
    // 加载当前页
    navigate(currentPage);
});

window.addEventListener("hashchange", () => {
    const h = location.hash.slice(1);
    if (h && h !== currentPage) navigate(h);
});
