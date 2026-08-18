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

// 收藏夹(localStorage)
const FAV_KEY = "gold_mes_favorites";
function getFavorites() {
    try { return JSON.parse(localStorage.getItem(FAV_KEY) || "[]"); }
    catch (e) { return []; }
}
function toggleFavorite(pageId) {
    let arr = getFavorites();
    if (arr.includes(pageId)) {
        arr = arr.filter(id => id !== pageId);
    } else {
        arr.unshift(pageId);
    }
    localStorage.setItem(FAV_KEY, JSON.stringify(arr));
    return arr.includes(pageId);
}

// Section 折叠状态(localStorage)
const COLLAPSE_KEY = "gold_mes_collapsed_sections";
function getCollapsed() {
    try { return JSON.parse(localStorage.getItem(COLLAPSE_KEY) || "[]"); }
    catch (e) { return []; }
}
function toggleCollapse(section) {
    let arr = getCollapsed();
    if (arr.includes(section)) {
        arr = arr.filter(s => s !== section);
    } else {
        arr.push(section);
    }
    localStorage.setItem(COLLAPSE_KEY, JSON.stringify(arr));
    return arr.includes(section);
}
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
    const favorites = getFavorites();
    let html = "";

    // 收藏夹(如果非空)
    if (favorites.length > 0) {
        html += `<div class="menu-section">`;
        html += `<div class="menu-section-title recent" data-section-toggle="⭐ 收藏夹">⭐ 收藏夹 <span class="section-count">${favorites.length}</span></div>`;
        favorites.forEach(pageId => {
            const item = findPage(pageId);
            if (!item) return;
            const active = item.id === currentPage ? "active" : "";
            html += renderMenuItem(item, active, '⭐ 收藏');
        });
        html += `</div>`;
    }

    // 最近访问(如果非空)
    if (recent.length > 0) {
        html += `<div class="menu-section">`;
        html += `<div class="menu-section-title recent" data-section-toggle="⏱ 最近访问">⏱ 最近访问 <span class="section-count">${recent.length}</span></div>`;
        recent.forEach(pageId => {
            const item = findPage(pageId);
            if (!item) return;
            const active = item.id === currentPage ? "active" : "";
            html += renderMenuItem(item, active, '⏱ 最近');
        });
        html += `</div>`;
    }

    const collapsed = getCollapsed();
    NAV.forEach(section => {
        const isCollapsed = collapsed.includes(section.section);
        html += `<div class="menu-section ${isCollapsed ? 'collapsed' : ''}" data-section="${escapeHtml(section.section)}">`;
        html += `<div class="menu-section-title" data-section-toggle="${escapeHtml(section.section)}">${section.section} <span class="section-count">${section.items.length}</span></div>`;
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
    const favActive = getFavorites().includes(item.id) ? 'active' : '';
    return `<a class="menu-item ${active}" href="#${item.id}" data-id="${item.id}" data-section="${escapeHtml(section)}" title="${escapeHtml(item.desc || item.name)}">
        <span class="icon">${item.icon}</span>
        <div class="item-main">
            <span class="item-name">${highlightKeyword(item.name, menuSearchKeyword)}</span>
            ${descHtml}
        </div>
        <button class="fav-star ${favActive}" data-fav-toggle="${item.id}" title="收藏/取消">★</button>
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
    // 找当前页所在 section
    let section = '其他';
    for (const sec of NAV) {
        if (sec.items.find(i => i.id === currentPage)) {
            section = sec.section;
            break;
        }
    }
    document.querySelector(".breadcrumb").innerHTML = `
        <a href="#dashboard" data-crumb="dashboard">🏠 车间</a>
        <span class="crumb-sep"> / </span>
        <a href="#${section.replace(/[^\w]/g, '_')}" data-crumb-section="${escapeHtml(section)}">${escapeHtml(section)}</a>
        <span class="crumb-sep"> / </span>
        <span class="crumb-current">${escapeHtml(page.name)}</span>
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
            // 表格工具条(搜索 + 排序)
            if (window.UI && window.UI.setupTableTools) {
                window.UI.setupTableTools(main);
            }
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
    // 首次加载显式渲染菜单(navigate 有短路条件可能不触发)
    renderMenu();
    updateBreadcrumb();
    // 绑定菜单点击
    document.querySelector(".sidebar").addEventListener("click", (e) => {
        // 收藏按钮
        const favBtn = e.target.closest('[data-fav-toggle]');
        if (favBtn) {
            e.preventDefault();
            e.stopPropagation();
            const pageId = favBtn.dataset.favToggle;
            toggleFavorite(pageId);
            renderMenu();
            window.toast && window.toast('success', toggleFavorite.last ? '⭐ 已添加收藏' : '✓ 已取消收藏');
            return;
        }
        // Section 折叠
        const secTitle = e.target.closest('[data-section-toggle]');
        if (secTitle) {
            e.preventDefault();
            e.stopPropagation();
            const sectionEl = secTitle.closest('.menu-section');
            const sec = sectionEl.dataset.section;
            if (sec) {
                toggleCollapse(sec);
                renderMenu();
            }
            return;
        }
        // 菜单项点击
        const link = e.target.closest(".menu-item");
        if (link) {
            e.preventDefault();
            navigate(link.dataset.id);
        }
    });
    // 顶栏菜单切换
    document.querySelector(".menu-toggle").addEventListener("click", toggleSidebar);
    // 搜索框(实时过滤菜单)
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
    // 面包屑点击(可跳转到 section 第一个页)
    document.querySelector(".breadcrumb").addEventListener("click", (e) => {
        const link = e.target.closest('a');
        if (!link) return;
        e.preventDefault();
        const section = link.dataset.crumbSection;
        if (section) {
            // 跳到该 section 的第一个页面
            const sec = NAV.find(s => s.section === section);
            if (sec) navigate(sec.items[0].id);
        } else if (link.dataset.crumb === 'dashboard') {
            navigate('dashboard');
        }
    });
    // 加载当前页
    navigate(currentPage);
});

window.addEventListener("hashchange", () => {
    const h = location.hash.slice(1);
    if (h && h !== currentPage) navigate(h);
});
