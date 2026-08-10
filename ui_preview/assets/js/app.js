// 伪 Odoo 17 — 敦煌金加工车间 ERP 离线预览
// 导航 + 页面切换

const NAV = [
    {section: "主数据", items: [
        {id: "measurement", name: "计量单位", icon: "⚖️", file: "page_measurement.html"},
        {id: "process_operation", name: "工艺工序", icon: "🔧", file: "page_process_operation.html"},
        {id: "process_route", name: "工艺路线模板", icon: "🛤️", file: "page_process_route.html"},
        {id: "workstation", name: "工位", icon: "🔲", file: "page_workstation.html"},
        {id: "equipment", name: "设备台账", icon: "⚙️", file: "page_equipment.html"},
    ]},
    {section: "金料与金价", items: [
        {id: "material_batch", name: "金料批次", icon: "💰", file: "page_material_batch.html"},
        {id: "price_engine", name: "实时金价", icon: "📈", file: "page_price_engine.html"},
        {id: "recycle", name: "旧金回收", icon: "♻️", file: "page_recycle.html"},
    ]},
    {section: "模具/蜡模", items: [
        {id: "mold", name: "模具台账", icon: "🔩", file: "page_mold.html"},
        {id: "wax", name: "蜡模管理", icon: "🕯️", file: "page_wax_model.html"},
    ]},
    {section: "生产执行", items: [
        {id: "workorder_report", name: "工序报工", icon: "📝", file: "page_workorder_report.html"},
        {id: "loss_trace", name: "损耗追溯", icon: "🔍", file: "page_loss_trace.html"},
        {id: "outsource", name: "委外加工", icon: "🤝", file: "page_outsource.html"},
        {id: "piece", name: "件级 SN", icon: "🔖", file: "page_piece.html"},
    ]},
    {section: "质量与印记", items: [
        {id: "qc", name: "质检记录", icon: "✅", file: "page_quality.html"},
        {id: "xrf", name: "XRF 含量检测", icon: "🔬", file: "page_xrf.html"},
        {id: "imprint", name: "印记记录", icon: "📍", file: "page_imprint.html"},
    ]},
    {section: "看板", items: [
        {id: "dashboard", name: "车间看板", icon: "📊", file: "page_dashboard.html"},
    ]},
    {section: "采购/销售(预留)", items: [
        {id: "procurement", name: "采购订单 (预留)", icon: "📦", file: "page_procurement.html"},
        {id: "sale", name: "销售订单 (预留)", icon: "🛒", file: "page_sale.html"},
    ]},
];

// 当前页
let currentPage = location.hash.slice(1) || "dashboard";

function renderMenu() {
    const sidebar = document.querySelector(".sidebar");
    if (!sidebar) return;
    let html = "";
    NAV.forEach(section => {
        html += `<div class="menu-section">`;
        html += `<div class="menu-section-title">${section.section}</div>`;
        section.items.forEach(item => {
            const active = item.id === currentPage ? "active" : "";
            html += `<a class="menu-item ${active}" href="#${item.id}" data-id="${item.id}">`;
            html += `<span class="icon">${item.icon}</span>`;
            html += `<span>${item.name}</span>`;
            if (item.id === "loss_trace") html += `<span class="badge">3</span>`;
            if (item.id === "mold") html += `<span class="badge">2</span>`;
            html += `</a>`;
        });
        html += `</div>`;
    });
    sidebar.innerHTML = html;
}

function navigate(pageId) {
    currentPage = pageId;
    location.hash = pageId;
    renderMenu();
    updateBreadcrumb();
    loadPage(pageId);
}

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
    main.innerHTML = '<div class="notice info">🔄 加载中...</div>';
    try {
        const resp = await fetch(`pages/${page.file}`);
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        const html = await resp.text();
        main.innerHTML = html;
    } catch (e) {
        main.innerHTML = `
            <div class="notice danger">
                ❌ 加载失败: ${e.message}
            </div>
            <div class="notice">
                注意: 本离线预览需要通过 HTTP 服务器访问,不能直接打开本地文件(file://)。
            </div>
        `;
    }
}

function toggleSidebar() {
    document.querySelector(".sidebar").classList.toggle("collapsed");
    document.querySelector(".main").classList.toggle("full");
}

document.addEventListener("DOMContentLoaded", () => {
    renderMenu();
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
    // 加载当前页
    navigate(currentPage);
});

window.addEventListener("hashchange", () => {
    const h = location.hash.slice(1);
    if (h && h !== currentPage) navigate(h);
});
