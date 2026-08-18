// 敦煌金 MES - 全局快捷键 / 命令面板 / Toast / 网络状态
// 加载: <script src="assets/js/shortcuts.js"></script>
// 依赖: window.UI(可选), window.API(可选)

(function () {
    'use strict';

    // ============================================================
    // 1. 全局快捷键
    // ============================================================

    const HOTKEYS = {
        // 导航
        'g d':     { desc: '车间看板',         goto: 'dashboard' },
        'g b':     { desc: '金料批次',         goto: 'material_batch' },
        'g w':     { desc: '工序报工',         goto: 'workorder_report' },
        'g m':     { desc: '维护工单',         goto: 'maintenance' },
        'g e':     { desc: '环境监测',         goto: 'environment' },
        'g h':     { desc: '危化品',           goto: 'hazardous_chemical' },
        'g i':     { desc: '金料盘点',         goto: 'inventory_count' },
        'g r':     { desc: '实时金价',         goto: 'price_engine' },

        // 操作
        '?':       { desc: '显示/隐藏快捷键面板', action: () => toggleCmdK(true) },
        '/':       { desc: '聚焦到搜索框',     action: () => document.querySelector('.navbar .search')?.focus() },
        'Escape':  { desc: '关闭弹窗/退出聚焦', action: () => {
            // 优先关闭 cmdk
            const cmdk = document.querySelector('.cmdk-overlay');
            if (cmdk) { cmdk.remove(); return; }
            // 退出聚焦
            if (document.activeElement && document.activeElement !== document.body) {
                document.activeElement.blur();
            }
        }},

        // 表单通用
        'mod+s':   { desc: '保存当前表单',     action: () => {
            const form = document.querySelector('form');
            if (form) {
                const btn = form.querySelector('button[type=submit], .btn-primary, .btn-gold');
                if (btn && !btn.matches(':disabled')) btn.click();
                else toast('info', '当前页没有可保存的表单');
            } else {
                toast('info', '当前页没有表单');
            }
        }},
    };

    // 修饰键检测(支持 Mac/Win/Linux)
    const isMac = navigator.platform.toUpperCase().includes('MAC');
    const MOD = isMac ? 'Meta' : 'Control';

    // 按键序列状态(g + g / g + b 双键导航)
    let pendingKey = null;
    let pendingTimer = null;
    const PENDING_TIMEOUT = 1000;

    function resetPending() {
        pendingKey = null;
        if (pendingTimer) {
            clearTimeout(pendingTimer);
            pendingTimer = null;
        }
    }

    function handleKey(e) {
        // 输入框 / textarea 不响应(避免误触)
        const tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
            // 仅 Esc / Ctrl+K 例外
            if (e.key !== 'Escape' && !(e.ctrlKey || e.metaKey)) return;
        }

        const key = e.key;
        const hasMod = e.ctrlKey || e.metaKey;
        const modPrefix = hasMod ? 'mod+' : '';

        // 单键
        const single = modPrefix + (key === ' ' ? 'Space' :
                              key.length === 1 ? key.toLowerCase() :
                              key);

        // 检查 mod+s 等带修饰键
        const hotkeyStr = (hasMod ? MOD + '+' : '') + (key === ' ' ? 'Space' :
                                                     key.length === 1 ? key.toLowerCase() :
                                                     key);

        // Ctrl/Cmd + K = 命令面板
        if ((e.ctrlKey || e.metaKey) && key === 'k') {
            e.preventDefault();
            toggleCmdK(true);
            return;
        }

        // 序列键(g + x)
        if (pendingKey) {
            const seq = pendingKey + ' ' + (key.length === 1 ? key.toLowerCase() : key);
            const action = HOTKEYS[seq];
            resetPending();
            if (action) {
                e.preventDefault();
                runAction(action);
                return;
            }
        }

        // 单键 / 修饰键
        const action = HOTKEYS[single] || HOTKEYS[hotkeyStr];
        if (action) {
            // Ctrl+K / Esc / ? 等需要 preventDefault
            if (hasMod || key === 'Escape' || key === '?' || key === '/') {
                e.preventDefault();
            }
            runAction(action);
            return;
        }

        // 准备进入序列(只对单字符 g 起效)
        if (key === 'g' && !hasMod) {
            pendingKey = 'g';
            pendingTimer = setTimeout(resetPending, PENDING_TIMEOUT);
            return;
        }
    }

    function runAction(action) {
        if (action.goto) {
            navigate(action.goto);
        } else if (action.action) {
            action.action();
        }
    }

    // ============================================================
    // 2. 命令面板 (Ctrl+K / ? 唤起)
    // ============================================================

    function toggleCmdK(forceOpen) {
        const existing = document.querySelector('.cmdk-overlay');
        if (existing && !forceOpen) {
            existing.remove();
            return;
        }
        if (existing && forceOpen) return;  // 已打开
        openCmdK();
    }

    function openCmdK() {
        const overlay = document.createElement('div');
        overlay.className = 'cmdk-overlay';
        overlay.innerHTML = `
            <div class="cmdk-panel" role="dialog" aria-label="命令面板">
                <input class="cmdk-input" placeholder="搜索菜单、页面、操作..." autofocus>
                <div class="cmdk-list"></div>
            </div>
        `;
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });
        document.body.appendChild(overlay);

        const input = overlay.querySelector('.cmdk-input');
        const list = overlay.querySelector('.cmdk-list');

        // 聚合菜单 + 快捷键
        const items = [];
        if (window.NAV) {
            window.NAV.forEach(section => {
                section.items.forEach(it => {
                    items.push({
                        type: 'nav',
                        icon: it.icon,
                        name: it.name,
                        desc: section.section,
                        action: () => navigate(it.id),
                    });
                });
            });
        }
        Object.entries(HOTKEYS).forEach(([k, v]) => {
            items.push({
                type: 'action',
                icon: '⌨️',
                name: v.desc,
                desc: v.goto ? `导航 → ${v.goto}` : '操作',
                shortcut: k,
                action: v.action || (() => v.goto && navigate(v.goto)),
            });
        });

        let activeIdx = 0;
        let filtered = items.slice();

        function render(filter) {
            filter = (filter || '').toLowerCase().trim();
            filtered = filter
                ? items.filter(it =>
                    it.name.toLowerCase().includes(filter) ||
                    (it.desc || '').toLowerCase().includes(filter) ||
                    (it.shortcut || '').toLowerCase().includes(filter)
                  )
                : items.slice();
            activeIdx = 0;
            if (!filtered.length) {
                list.innerHTML = '<div class="cmdk-empty">无匹配结果</div>';
                return;
            }
            list.innerHTML = filtered.slice(0, 50).map((it, i) => `
                <div class="cmdk-item ${i === activeIdx ? 'active' : ''}" data-idx="${i}">
                    <span class="icon">${it.icon || ''}</span>
                    <span class="name">${escapeHtml(it.name)}</span>
                    <span class="desc">${escapeHtml(it.desc || '')}</span>
                    ${it.shortcut ? `<span class="shortcut">${escapeHtml(it.shortcut)}</span>` : ''}
                </div>
            `).join('');
        }

        function commit() {
            const it = filtered[activeIdx];
            if (it) {
                it.action();
                overlay.remove();
            }
        }

        input.addEventListener('input', () => render(input.value));
        input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIdx = Math.min(filtered.length - 1, activeIdx + 1);
                render(input.value);
                scrollActiveIntoView();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIdx = Math.max(0, activeIdx - 1);
                render(input.value);
                scrollActiveIntoView();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                commit();
            } else if (e.key === 'Escape') {
                overlay.remove();
            }
        });

        list.addEventListener('click', (e) => {
            const item = e.target.closest('.cmdk-item');
            if (!item) return;
            activeIdx = Number(item.dataset.idx);
            commit();
        });

        function scrollActiveIntoView() {
            const active = list.querySelector('.cmdk-item.active');
            if (active) active.scrollIntoView({ block: 'nearest' });
        }

        render('');
        setTimeout(() => input.focus(), 0);
    }

    // ============================================================
    // 3. Toast 通知
    // ============================================================

    function ensureToastContainer() {
        let c = document.querySelector('.toast-container');
        if (!c) {
            c = document.createElement('div');
            c.className = 'toast-container';
            document.body.appendChild(c);
        }
        return c;
    }

    function toast(type, msg, durationMs = 3000) {
        const container = ensureToastContainer();
        const el = document.createElement('div');
        el.className = `toast ${type || ''}`;
        el.textContent = msg;
        container.appendChild(el);
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateX(100%)';
            el.style.transition = 'all 0.25s';
            setTimeout(() => el.remove(), 260);
        }, durationMs);
    }

    // ============================================================
    // 4. 网络状态指示器
    // ============================================================

    function setupNetStatus() {
        const online = () => {
            const existing = document.querySelector('.net-status');
            if (existing) existing.remove();
            toast('success', '✓ 网络已恢复', 2000);
        };
        const offline = () => {
            if (document.querySelector('.net-status')) return;
            const el = document.createElement('div');
            el.className = 'net-status show offline';
            el.innerHTML = '<span class="pulse-dot"></span><span>📡 离线模式 — 数据本地缓存</span>';
            document.body.appendChild(el);
            toast('warning', '⚠ 网络中断,操作将本地缓存', 4000);
        };
        window.addEventListener('online', online);
        window.addEventListener('offline', offline);
        if (!navigator.onLine) offline();
    }

    // ============================================================
    // 5. 工具函数
    // ============================================================

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;',
            '"': '&quot;', "'": '&#39;',
        }[c]));
    }

    // ============================================================
    // 6. 注入 Skip Link + 焦点环增强
    // ============================================================

    function injectSkipLink() {
        if (document.querySelector('.skip-link')) return;
        const link = document.createElement('a');
        link.href = '#main-content';
        link.className = 'skip-link';
        link.textContent = '跳转到主内容';
        document.body.insertBefore(link, document.body.firstChild);
        const main = document.querySelector('.main');
        if (main && !main.id) main.id = 'main-content';
    }

    // ============================================================
    // 7. 启动
    // ============================================================

    document.addEventListener('DOMContentLoaded', () => {
        document.addEventListener('keydown', handleKey);
        setupNetStatus();
        // 延迟注入,等 app.js 渲染完 navbar
        setTimeout(() => {
            injectSkipLink();
            attachShortcutHints();
        }, 200);
    });

    // 给主按钮附加快捷键徽章
    function attachShortcutHints() {
        const hints = [
            { sel: '.navbar .search',            text: '/' },
            { sel: '[data-shortcut]',           text: null },  // 自动从 data-shortcut 属性读
            { sel: '.btn.btn-primary, .btn-gold', text: 'Ctrl+S' },
        ];
        hints.forEach(h => {
            if (h.text === null) return;
            document.querySelectorAll(h.sel).forEach(el => {
                if (el.querySelector('.kbd-hint')) return;
                const kbd = document.createElement('span');
                kbd.className = 'kbd-hint';
                kbd.textContent = h.text;
                el.appendChild(kbd);
            });
        });
        // 任何 data-shortcut 属性的元素自动添加徽章
        document.querySelectorAll('[data-shortcut]').forEach(el => {
            if (el.querySelector('.kbd-hint')) return;
            const kbd = document.createElement('span');
            kbd.className = 'kbd-hint';
            kbd.textContent = el.dataset.shortcut;
            el.appendChild(kbd);
        });
    }

    // ============================================================
    // 导出公共 API
    // ============================================================

    window.shortcuts = {
        toast,
        navigate,           // 由 app.js 设置
        HOTKEYS,
        toggleCmdK,
        isMac,
    };

    // 兼容老代码:toast 暴露成 window.toast
    window.toast = toast;

})();