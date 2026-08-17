# UI 美化 v1 — 视觉抛光

> 5 项视觉强化交付物
> 总增量:+30 KB / +700 行(CSS +600 行 + JS 新建 9 KB)

## 🎨 美化清单

### 1. 金色 Spinner + 骨架屏

替换原本朴素的 `🔄 加载中...` 文字:

```html
<div class="loading-state">
    <div class="spinner-gold lg"></div>
    <div class="loading-text">正在加载 金料批次...</div>
</div>
```

**特性**:
- 金色渐变圆环旋转
- 三种尺寸:`sm` (20px) / 默认 (48px) / `lg` (64px)
- 金色光晕跟随,弱光环境也清晰可见
- 文案带脉冲呼吸

骨架屏(数据加载期间占位):
```html
<span class="skeleton skeleton-line long"></span>      <!-- 100% 宽 -->
<span class="skeleton skeleton-line medium"></span>    <!-- 70% 宽 -->
<span class="skeleton skeleton-line short"></span>     <!-- 40% 宽 -->
<span class="skeleton skeleton-circle"></span>         <!-- 圆形 -->
<span class="skeleton skeleton-card"></span>           <!-- 卡片 -->
```

**特性**:左到右 shimmer 流动 1.5s,模拟"加载中"感觉

---

### 2. 空状态组件

所有"无数据"场景统一展示:

```html
<div class="empty-state">
    <div class="empty-state-icon">💰</div>
    <div class="empty-state-title">暂无金料批次</div>
    <div class="empty-state-desc">金库空空如也,请先入库金料或等待供应商来料</div>
    <button class="btn btn-primary btn-ripple">新建批次</button>
</div>
```

**特性**:
- 80×80 圆形图标,内阴影 + 金色边框
- 标题 + 描述 + 主操作三段式
- 渐入动画 0.4s
- 已应用到 `material_batch` 渲染器(无批次时显示)

---

### 3. 玻璃拟态卡片 + 悬浮渐变边框

KPI 卡片悬浮时:
```css
.kpi-card {
    transition: all 0.25s;
    /* 渐变边框 mask 技巧 */
}
.kpi-card::before {
    background: linear-gradient(135deg, transparent, var(--gold-border) 40%, transparent);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
}
.kpi-card:hover::before { opacity: 1; }
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg), var(--shadow-gold-glow);
}
```

**效果**:鼠标悬浮 → 卡片上浮 3px + 金色边框渐变显现 + 金色光晕

通用玻璃面板:
```html
<div class="glass-panel">...</div>
```
backdrop-filter: blur(12px) saturate(180%)

---

### 4. 数字滚动动画(count-up)

KPI 数字从 0 滚动到目标值,带弹性曲线:

```html
<span class="big-number gold" data-count="28">0</span>
<span class="big-number" data-count="5661943" data-decimals="0">¥0</span>
<span class="big-number" data-count="99.5" data-decimals="1">0</span><span class="unit">%</span>
```

```js
window.UI.autoCountUp();  // 自动扫描 [data-count] 元素
```

**特性**:
- 800ms ease-out cubic 曲线
- `font-variant-numeric: tabular-nums` 等宽数字,不抖动
- 滚动期间金色发光 + 文案变色,结束后恢复

辅助函数:
```js
window.UI.formatNumber(n, { decimals: 2, suffix: 'g' })  // 1,234.56g
window.UI.formatCurrency(1234.5)                         // ¥1,234.50
window.UI.formatWeight(5.18)                              // 5.180 g
window.UI.formatPercent(99.5, 2)                          // 99.50%
window.UI.formatCompact(1234567)                          // 1.2M
```

---

### 5. 微交互(涟漪 + 交错入场)

按钮涟漪(按下时从中心扩散):
```html
<button class="btn btn-ripple">提交报工</button>
```
`::after` 伪元素 + `@keyframes ripple-expand`,0.5s 扩散到 300px 圆环后消失。

列表交错入场(stagger):
```html
<tbody class="stagger-in">
  <tr>...</tr>  <!-- 0.02s -->
  <tr>...</tr>  <!-- 0.06s -->
  ...
</tbody>
```
每行延迟 0.04s 渐入,营造"瀑布"效果。

---

### 6. 状态徽章统一组件

```js
window.UI.statusBadgeHTML('passed', '合格')
// → <span class="status-badge success">合格</span>

window.UI.statusBadgeHTML('alarm', '超限')
// → <span class="status-badge danger">超限</span>
```

**类型**:`success / warning / danger / info / muted`
**特性**:6px 发光圆点 + 状态文字,色盲友好(文字 + 圆点双编码)

---

### 7. 其他细节

- **差异着色**:`+0.050` 绿 / `-0.030` 红 / `0` 灰
- **页面头部**:渐变背景 `linear-gradient(90deg, var(--gold-muted), transparent)`
- **表格行悬浮**:左侧 2px 金色边线 + 渐变背景
- **大数字**:透明色文字 + 渐变填充(高级感)
- **背景光斑动画**:`body::before` 20s 慢速浮动金色光斑

---

## 📊 文件变化

```
assets/css/common.css        51 KB(+10 KB,+600 行)
assets/js/beautify.js        9 KB(新建,+~270 行)
assets/js/renderers.js       29 KB(应用美化)
assets/js/app.js             7 KB(loadingHTML)
index.html                   +1 行(引入 beautify.js)
```

**总 UI 包**:96 KB → 130 KB(增加 35%)

---

## 🎯 实际效果(dashboard 页)

刷新 dashboard 页看到:

```
┌────────────────────────────────────────────────────────┐
│ 车间看板                              [🔄 刷新]         │
├────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│ │ 当日完工  │ │ 进行中   │ │ 超耗预警 │ │ 当前金价  │  │
│ │   28     │ │    5     │ │    1     │ │ ¥582.50  │  │
│ │ 件级SN   │ │ 生产订单 │ │  需复盘  │ │  /g     │  │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│ │ 库存估值  │ │ 平均损耗 │ │ XRF合格率 │ │ 油压/失蜡 │  │
│ │ ¥5,661,943│ │ 3.85%   │ │ 98.5%    │ │ 5 单     │  │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│ ┌──────────────────────────────────────────────────┐ │
│ │ 🟡 需关注  📊 数据来自 /api/v1/dashboard/kpi  ⌨ │ │
│ │   Ctrl+K 打开命令面板                           │ │
│ └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘

加载过程:
0ms:   4 个骨架卡片(脉冲流动)
200ms: 数据到达 → 4 个大数字从 0 滚动到目标值
      ease-out cubic,800ms 完成,数字带金色光晕
```

---

## 🧪 验证

- ✅ 105/105 自动化测试无回归
- ✅ 所有 JS 语法 OK
- ✅ 全部静态资源 200

## 🔮 浏览器立即验证

打开 http://localhost:8080:

1. **刷新 dashboard 页** → 看数字从 0 滚动到目标值
2. **打开金料批次** → 看交错入场动画
4. **F12 → Network → Slow 3G** → 看骨架屏 shimmer 效果
5. **Console 输入** `window.UI.formatCurrency(1234567.89)` 看格式化

---

## 📝 后续可继续(可选)

- 表格渲染改用 virtual scrolling(1000+ 行性能)
- Dashboard 添加 Chart.js 折线图(损耗趋势)
- PWA + 添加到主屏幕
- 主题切换(暗/亮)
- i18n 多语言

继续 P1 还是先看效果?