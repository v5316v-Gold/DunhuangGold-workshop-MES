// 敦煌金 MES - UI 美化辅助
// 数字格式化 / 滚动动画 / 加载态 / 空状态
// 加载: <script src="assets/js/beautify.js"></script>
// 依赖: 无

(function () {
    'use strict';

    // ============================================================
    // 1. 数字格式化
    // ============================================================

    /**
     * 通用数字格式化
     * @param {number} n     - 数字
     * @param {object} opts  - { decimals, locale, unit, suffix }
     * @returns {string}
     */
    function formatNumber(n, opts = {}) {
        if (n === null || n === undefined || isNaN(n)) return '—';
        const decimals = opts.decimals !== undefined ? opts.decimals : 0;
        const locale = opts.locale || 'zh-CN';

        let formatted;
        if (Math.abs(n) >= 10000 && !opts.decimals) {
            // 大数字用 locale 格式(自动加千分位)
            formatted = n.toLocaleString(locale, { maximumFractionDigits: 2 });
        } else {
            formatted = n.toLocaleString(locale, {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals,
            });
        }
        if (opts.unit) formatted += opts.unit;
        if (opts.suffix) formatted += opts.suffix;
        return formatted;
    }

    /** 货币格式化: ¥1,234.56 */
    function formatCurrency(n, decimals = 2) {
        return '¥' + formatNumber(n, { decimals, locale: 'zh-CN' });
    }

    /** 重量格式化: 5.250g (3 位小数) */
    function formatWeight(n) {
        return formatNumber(n, { decimals: 3 }) + ' g';
    }

    /** 百分比: 99.50% */
    function formatPercent(n, decimals = 1) {
        return formatNumber(n, { decimals }) + '%';
    }

    /** 大数字智能缩写: 12345 → 12.3k / 1234567 → 1.2M */
    function formatCompact(n) {
        if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(1) + 'B';
        if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + 'M';
        if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'k';
        return n.toString();
    }

    // ============================================================
    // 2. 数字滚动动画(count-up)
    // ============================================================

    /**
     * 从 0 滚动到目标值
     * @param {HTMLElement|string} target - 元素 / 选择器
     * @param {number}        endValue   - 目标值
     * @param {object}        opts - { duration, decimals, prefix, suffix }
     */
    function countUp(target, endValue, opts = {}) {
        const el = typeof target === 'string' ? document.querySelector(target) : target;
        if (!el) return;
        const duration = opts.duration || 800;
        const decimals = opts.decimals !== undefined ? opts.decimals : 0;
        const start = performance.now();
        const startValue = 0;

        el.classList.add('number-roll', 'updating');

        function step(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = startValue + (endValue - startValue) * eased;
            el.textContent = formatNumber(current, {
                decimals,
                unit: opts.suffix || '',
            });
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                el.textContent = formatNumber(endValue, {
                    decimals,
                    unit: opts.suffix || '',
                });
                el.classList.remove('updating');
            }
        }
        requestAnimationFrame(step);
    }

    /** 自动扫描页面上所有 .number-roll + data-count 属性,自动滚动 */
    function autoCountUp() {
        document.querySelectorAll('[data-count]').forEach(el => {
            const value = Number(el.dataset.count);
            const decimals = el.dataset.decimals ? Number(el.dataset.decimals) : 0;
            if (!isNaN(value)) countUp(el, value, { decimals });
        });
    }

    // ============================================================
    // 3. 加载状态(spinner + 骨架屏)
    // ============================================================

    /** 标准加载态(spinner + 文案) */
    function loadingHTML(text = '加载中...', size = '') {
        const spinner = `<div class="spinner-gold ${size}"></div>`;
        return `
            <div class="loading-state">
                ${spinner}
                <div class="loading-text">${escapeHtml(text)}</div>
            </div>
        `;
    }

    /** 骨架屏 - 表格行 */
    function skeletonRows(count = 5) {
        let html = '';
        for (let i = 0; i < count; i++) {
            html += `
                <tr>
                    <td><span class="skeleton skeleton-line long"></span></td>
                    <td><span class="skeleton skeleton-line medium"></span></td>
                    <td><span class="skeleton skeleton-line short"></span></td>
                    <td><span class="skeleton skeleton-line medium"></span></td>
                </tr>
            `;
        }
        return html;
    }

    /** 骨架屏 - KPI 卡片 */
    function skeletonCards(count = 4) {
        let html = '<div class="kpi-cards">';
        for (let i = 0; i < count; i++) {
            html += `
                <div class="kpi-card">
                    <span class="skeleton skeleton-line short" style="height:14px"></span>
                    <span class="skeleton skeleton-line long" style="height:36px;margin-top:12px;display:block"></span>
                </div>
            `;
        }
        html += '</div>';
        return html;
    }

    // ============================================================
    // 4. 空状态(empty state)
    // ============================================================

    /**
     * 标准空状态
     * @param {object} opts - { icon, title, desc, actionLabel, actionHref, actionOnClick }
     */
    function emptyStateHTML(opts = {}) {
        const {
            icon = '📭',
            title = '暂无数据',
            desc = '当前条件下没有记录',
            actionLabel = '',
            actionHref = '',
            actionOnClick = '',
        } = opts;
        let actionBtn = '';
        if (actionLabel) {
            if (actionHref) {
                actionBtn = `<a href="${actionHref}" class="btn btn-primary">${escapeHtml(actionLabel)}</a>`;
            } else if (actionOnClick) {
                actionBtn = `<button class="btn btn-primary" onclick="${actionOnClick}">${escapeHtml(actionLabel)}</button>`;
            } else {
                actionBtn = `<button class="btn btn-primary btn-ripple">${escapeHtml(actionLabel)}</button>`;
            }
        }
        return `
            <div class="empty-state">
                <div class="empty-state-icon">${icon}</div>
                <div class="empty-state-title">${escapeHtml(title)}</div>
                <div class="empty-state-desc">${escapeHtml(desc)}</div>
                ${actionBtn}
            </div>
        `;
    }

    // ============================================================
    // 5. 状态徽章
    // ============================================================

    function statusBadgeHTML(state, label) {
        const typeMap = {
            passed: 'success',
            available: 'success',
            done: 'success',
            confirmed: 'success',
            locked: 'info',
            draft: 'muted',
            pending: 'muted',
            counting: 'info',
            inspecting: 'info',
            failed: 'danger',
            scrapped: 'muted',
            scrap: 'danger',
            locked: 'warning',
            available: 'success',
            depleted: 'muted',
            normal: 'success',
            alarm: 'danger',
            running: 'success',
            maintenance: 'warning',
            idle: 'muted',
            in_progress: 'info',
        };
        const type = typeMap[state] || 'info';
        return `<span class="status-badge ${type}">${escapeHtml(label || state)}</span>`;
    }

    // ============================================================
    // 6. 数字着色(盈/亏/正/负)
    // ============================================================

    function diffColor(diff, unit = '') {
        if (typeof diff !== 'number') return '';
        const cls = diff > 0 ? 'text-success' : diff < 0 ? 'text-danger' : 'text-muted';
        const sign = diff > 0 ? '+' : '';
        return `<span class="${cls}">${sign}${formatNumber(diff, { decimals: 3 })}${unit}</span>`;
    }

    // ============================================================
    // 7. 工具函数
    // ============================================================

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;',
            '"': '&quot;', "'": '&#39;',
        }[c]));
    }

    /** 延迟辅助 */
    function delay(ms) {
        return new Promise(r => setTimeout(r, ms));
    }

    // ============================================================
    // 页面内快速搜索:表格过滤 + 列排序
    // ============================================================

    /**
     * 给容器内所有 table 加可过滤 + 可排序 + 导出 工具条
     * @param {string|HTMLElement} container - 容器选择符或元素
     * @param {object} opts - { searchable, sortable, exportable, filenameBase }
     */
    function setupTableTools(container, opts = {}) {
        const { searchable = true, sortable = true, exportable = true } = opts;
        const c = typeof container === 'string' ? document.querySelector(container) : container;
        if (!c) return;
        const tables = c.querySelectorAll('table');
        tables.forEach(t => {
            if (t.dataset.tooled === '1') return;
            t.dataset.tooled = '1';
            if (searchable) attachSearch(t, c);
            if (sortable) attachSort(t);
            // 导出按钮: 等 export.js (CDN) 加载后再加
            if (exportable) {
                const tryAttach = () => {
                    if (window.exporter) {
                        const base = opts.filenameBase
                            || t.closest('.card')?.querySelector('h3')?.textContent
                            || c.querySelector('.page-header h1')?.textContent
                            || 'export';
                        const title = base.replace(/[^\w\u4e00-\u9fa5-]+/g, '-');
                        if (!t.dataset.exportAttached) {
                            window.exporter.attachExportButtons(t, title);
                        }
                    } else {
                        setTimeout(tryAttach, 200);
                    }
                };
                tryAttach();
            }
        });
    }

    function attachSearch(table, container) {
        // 在 table 上方加一个搜索条
        const wrap = document.createElement('div');
        wrap.className = 'table-tools';
        wrap.innerHTML = `
            <input type="text" class="table-search" placeholder="🔍 在表格内筛选 (行内任意字段)">
            <span class="table-search-count">${table.tBodies[0]?.rows.length || 0} 行</span>
        `;
        table.parentNode.insertBefore(wrap, table);
        const input = wrap.querySelector('.table-search');
        const count = wrap.querySelector('.table-search-count');
        const originalBg = table.tBodies[0] ? Array.from(table.tBodies[0].rows).map(r => r.style.display) : [];
        input.addEventListener('input', () => {
            const k = input.value.toLowerCase().trim();
            let visible = 0;
            if (!table.tBodies[0]) return;
            Array.from(table.tBodies[0].rows).forEach((row, i) => {
                const text = row.textContent.toLowerCase();
                const match = !k || text.includes(k);
                row.style.display = match ? '' : 'none';
                if (match) visible++;
            });
            count.textContent = `${visible} / ${table.tBodies[0].rows.length} 行`;
        });
    }

    function attachSort(table) {
        // 给 thead th 加点击排序
        if (!table.tHead) return;
        const ths = table.tHead.querySelectorAll('th');
        ths.forEach((th, idx) => {
            // 跳过 checkbox / action 列
            if (th.querySelector('input[type=checkbox]')) return;
            th.classList.add('sortable-th');
            th.addEventListener('click', () => sortBy(table, idx, th));
        });
    }

    let lastSortCol = -1, lastSortDir = 1;
    function sortBy(table, colIdx, th) {
        if (!table.tBodies[0]) return;
        const rows = Array.from(table.tBodies[0].rows);
        const dir = (lastSortCol === colIdx) ? -lastSortDir : 1;
        rows.sort((a, b) => {
            const ac = a.cells[colIdx]?.textContent.trim() || '';
            const bc = b.cells[colIdx]?.textContent.trim() || '';
            // 尝试数字
            const an = parseFloat(ac.replace(/[^\d.-]/g, ''));
            const bn = parseFloat(bc.replace(/[^\d.-]/g, ''));
            if (!isNaN(an) && !isNaN(bn)) return (an - bn) * dir;
            return ac.localeCompare(bc) * dir;
        });
        rows.forEach(r => table.tBodies[0].appendChild(r));
        lastSortCol = colIdx;
        lastSortDir = dir;
        // 视觉指示
        th.parentNode.querySelectorAll('th').forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
        th.classList.add(dir > 0 ? 'sort-asc' : 'sort-desc');
    }

    // ============================================================
    // 8. 暴露公共 API
    // ============================================================

    const beautify = {
        formatNumber, formatCurrency, formatWeight, formatPercent, formatCompact,
        countUp, autoCountUp,
        loadingHTML, skeletonRows, skeletonCards,
        emptyStateHTML,
        statusBadgeHTML, diffColor,
        delay, escapeHtml,
        setupTableTools,
    };

    // 兼容老代码: window.UI 提供这些函数
    window.UI = Object.assign(window.UI || {}, beautify);
    window.beautify = beautify;

})();