// 敦煌金 ERP - 报表导出 (Excel / PDF)
// 依赖: SheetJS (XLSX), jsPDF, jsPDF-AutoTable (CDN 引入)
//
// 工具函数:
//   exportToExcel(data/table, filename, opts)
//   exportToPDF(data/table, filename, opts)
//   exportTableActions(tableEl, filenameBase) - 给 table 加按钮条
//   downloadBlob(blob, filename) - 触发浏览器下载

(function () {
    'use strict';

    // ============================================================
    // 1. 通用下载
    // ============================================================

    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    // ============================================================
    // 2. 从 <table> 元素抽数据
    // ============================================================

    function tableToData(table) {
        if (!table || !table.tHead) return { columns: [], rows: [] };
        const ths = Array.from(table.tHead.querySelectorAll('th'));
        const columns = ths.map((th, i) => {
            // 跳过 checkbox 列
            if (th.querySelector('input[type=checkbox]')) return null;
            // 取 data-field 优先,否则 textContent
            const text = th.textContent.trim();
            return text || `col_${i}`;
        }).filter(Boolean);
        const rows = [];
        if (table.tBodies[0]) {
            Array.from(table.tBodies[0].rows).forEach(tr => {
                if (tr.style.display === 'none') return;  // 跳过被搜索隐藏的
                const cells = Array.from(tr.cells);
                const obj = {};
                cells.forEach((td, i) => {
                    const col = columns[i];
                    if (!col) return;
                    obj[col] = td.textContent.trim();
                });
                if (Object.keys(obj).length) rows.push(obj);
            });
        }
        return { columns, rows };
    }

    // ============================================================
    // 3. Excel 导出
    // ============================================================

    /**
     * 导出为 Excel
     * @param {string|HTMLElement|Array} input - table 选择器/元素 或 数据数组
     * @param {string} filename - 文件名(不含扩展名)
     * @param {object} opts - { columns, sheetName, creator, freezeHeader, columnWidths }
     */
    function exportToExcel(input, filename, opts = {}) {
        if (typeof XLSX === 'undefined') {
            window.toast && window.toast('error', 'Excel 库未加载');
            return;
        }
        let columns, rows;
        if (typeof input === 'string' || input instanceof HTMLElement) {
            const el = typeof input === 'string' ? document.querySelector(input) : input;
            const data = tableToData(el);
            columns = data.columns;
            rows = data.rows;
        } else if (Array.isArray(input)) {
            rows = input;
            columns = opts.columns || (rows[0] ? Object.keys(rows[0]) : []);
        } else {
            window.toast && window.toast('error', '不支持的输入类型');
            return;
        }
        if (!rows.length) {
            window.toast && window.toast('warning', '没有数据可导出');
            return;
        }
        // 构建 worksheet 数据(列头 + 行)
        const wsData = [
            columns,
            ...rows.map(r => columns.map(c => r[c] || ''))
        ];
        const ws = XLSX.utils.aoa_to_sheet(wsData);
        // 设置列宽
        if (opts.columnWidths) {
            ws['!cols'] = opts.columnWidths.map(w => ({ wch: w }));
        } else {
            ws['!cols'] = columns.map(c => ({ wch: Math.max(12, c.length * 2.5) }));
        }
        // 冻结首行
        if (opts.freezeHeader !== false) {
            ws['!freeze'] = { xSplit: 0, ySplit: 1 };
        }
        // 样式(列头加粗)
        if (ws['!ref']) {
            // SheetJS 社区版不直接支持 cell-level 样式,跳过
        }
        // 创建 workbook
        const wb = XLSX.utils.book_new();
        const sheetName = opts.sheetName || 'Sheet1';
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
        // 元数据
        if (opts.creator) wb.Props = { Creator: opts.creator };
        // 写入文件
        const ext = '.xlsx';
        const fn = (filename || 'export') + ext;
        XLSX.writeFile(wb, fn);
        window.toast && window.toast('success', `✓ 已导出 ${fn} (${rows.length} 行)`);
    }

    // ============================================================
    // 4. PDF 导出
    // ============================================================

    /**
     * 导出为 PDF
     * @param {string|HTMLElement|Array} input - table 或数据数组
     * @param {string} filename - 文件名
     * @param {object} opts - { title, subtitle, columns, orientation, creator }
     */
    function exportToPDF(input, filename, opts = {}) {
        if (typeof window.jspdf === 'undefined' || !window.jspdf.jsPDF) {
            window.toast && window.toast('error', 'PDF 库未加载');
            return;
        }
        let columns, rows;
        if (typeof input === 'string' || input instanceof HTMLElement) {
            const el = typeof input === 'string' ? document.querySelector(input) : input;
            const data = tableToData(el);
            columns = data.columns;
            rows = data.rows;
        } else if (Array.isArray(input)) {
            rows = input;
            columns = opts.columns || (rows[0] ? Object.keys(rows[0]) : []);
        } else {
            window.toast && window.toast('error', '不支持的输入类型');
            return;
        }
        if (!rows.length) {
            window.toast && window.toast('warning', '没有数据可导出');
            return;
        }
        // 创建 PDF (A4 横向适合宽表)
        const { jsPDF } = window.jspdf;
        const orientation = opts.orientation || (columns.length > 5 ? 'landscape' : 'portrait');
        const pdf = new jsPDF({ orientation, unit: 'mm', format: 'a4' });
        // 标题块
        const pageW = pdf.internal.pageSize.getWidth();
        const title = opts.title || filename || '报表';
        pdf.setFontSize(16);
        pdf.setTextColor(40, 40, 40);
        pdf.text(title, 14, 15);
        // 副标题(时间 + 来源)
        pdf.setFontSize(9);
        pdf.setTextColor(120, 120, 120);
        const subtitle = opts.subtitle || `导出时间: ${new Date().toLocaleString('zh-CN')} · 共 ${rows.length} 行`;
        pdf.text(subtitle, 14, 22);
        // 装饰线
        pdf.setDrawColor(212, 175, 55);  // 金色
        pdf.setLineWidth(0.5);
        pdf.line(14, 25, pageW - 14, 25);
        // 表格数据
        const body = rows.map(r => columns.map(c => String(r[c] || '')));
        pdf.autoTable({
            head: [columns],
            body,
            startY: 30,
            theme: 'grid',
            headStyles: {
                fillColor: [212, 175, 55],   // 金色
                textColor: [20, 20, 20],
                fontStyle: 'bold',
                fontSize: 9,
            },
            bodyStyles: {
                fontSize: 8,
                textColor: [40, 40, 40],
            },
            alternateRowStyles: { fillColor: [248, 246, 240] },
            margin: { left: 14, right: 14 },
            styles: { overflow: 'linebreak', cellPadding: 2 },
        });
        // 页脚
        const pageCount = pdf.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            pdf.setPage(i);
            pdf.setFontSize(8);
            pdf.setTextColor(150, 150, 150);
            pdf.text(
                `${i} / ${pageCount}  ·  敦煌金加工车间 ERP`,
                pageW / 2, pdf.internal.pageSize.getHeight() - 6,
                { align: 'center' }
            );
        }
        const ext = '.pdf';
        const fn = (filename || 'export') + ext;
        pdf.save(fn);
        window.toast && window.toast('success', `✓ 已导出 ${fn} (${rows.length} 行, ${pageCount} 页)`);
    }

    // ============================================================
    // 5. 给表格添加导出按钮条
    // ============================================================

    /**
     * 给指定 table 上方加 [导出 Excel] [导出 PDF] 按钮
     * @param {string|HTMLElement} table - table 选择器/元素
     * @param {string} filenameBase - 文件名(不含扩展名)
     * @param {object} opts - { title, columns }
     */
    function attachExportButtons(table, filenameBase, opts = {}) {
        const t = typeof table === 'string' ? document.querySelector(table) : table;
        if (!t) return;
        if (t.dataset.exportAttached === '1') return;
        t.dataset.exportAttached = '1';
        const base = filenameBase || (opts.title || t.closest('.card')?.querySelector('h3')?.textContent || 'export')
            .replace(/[^\w\u4e00-\u9fa5-]+/g, '-');
        // 在 table-tools 同一行追加按钮(若已有则合并)
        let toolbar = t.parentElement.querySelector(':scope > .table-tools');
        if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.className = 'table-tools';
            t.parentNode.insertBefore(toolbar, t);
        }
        const search = toolbar.querySelector('.table-search');
        // 按钮容器
        const btnWrap = document.createElement('div');
        btnWrap.className = 'table-export-btns';
        const title = opts.title || base;
        btnWrap.innerHTML = `
            <button class="btn btn-ripple export-excel" data-fmt="xlsx" style="min-height:32px;padding:4px 12px;font-size:12px">
                📊 Excel
            </button>
            <button class="btn btn-ripple export-pdf" data-fmt="pdf" style="min-height:32px;padding:4px 12px;font-size:12px">
                📄 PDF
            </button>
        `;
        if (search) {
            // 搜索框 + 按钮组一起
            toolbar.appendChild(btnWrap);
        } else {
            toolbar.insertBefore(btnWrap, t);
        }
        // 绑定事件(只绑定到当前 toolbar)
        const onClick = (e) => {
            const btn = e.target.closest('button');
            if (!btn) return;
            const fmt = btn.dataset.fmt;
            const ts = new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-');
            const fn = `${base}-${ts}`;
            if (fmt === 'xlsx') {
                exportToExcel(t, fn, { title, creator: '敦煌金 ERP' });
            } else {
                exportToPDF(t, fn, { title, subtitle: `导出时间: ${new Date().toLocaleString('zh-CN')}` });
            }
        };
        btnWrap.addEventListener('click', onClick);
    }

    /**
     * 批量为容器内所有 table 加导出按钮
     * @param {string|HTMLElement} container
     * @param {string} filenameBase
     */
    function setupExportButtons(container, filenameBase) {
        const c = typeof container === 'string' ? document.querySelector(container) : container;
        if (!c) return;
        const tables = c.querySelectorAll('table');
        tables.forEach((t, i) => {
            const base = i === 0 ? filenameBase : `${filenameBase}-${i}`;
            attachExportButtons(t, base);
        });
    }

    // ============================================================
    // 导出公共 API
    // ============================================================

    const exporter = {
        exportToExcel,
        exportToPDF,
        tableToData,
        attachExportButtons,
        setupExportButtons,
        downloadBlob,
    };

    window.exporter = exporter;
    // 兼容老代码
    window.UI = Object.assign(window.UI || {}, exporter);

})();