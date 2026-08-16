# Phase 1: P0 Bug 修复 + CI 真绿 + 跨平台兼容

> 4 commits · 13 files · +461 / −392 · 综合 7.2 → 7.5 (估)

## 🎯 目标

清理 v1.0 基线里**真实存在的 5 个 P0 bug + 1 个隐藏 bug(BOM)**,让 CI 真正跑通、validate 脚本跨平台可用、模型状态机符合 Odoo 标准模式。

---

## 🐛 Bug 清单

| # | 严重度 | Bug | 影响 |
|---|--------|-----|------|
| **1.1** | 🔴 P0 | CI workflow 路径写错(`dunhuang_gold_mes` vs 实际 `dunhuanggold_workshop_mes`) | README 上 CI 绿 badge 是**假象**,每次 push 都红 |
| **1.2** | 🔴 P0 | validate 脚本输出 Unicode 在 Windows GBK 控制台崩溃 | Windows 开发者完全无法本地验证 |
| **1.2+** | 🟡 P1 | **额外发现** 7 个源文件带 UTF-8 BOM + ir.model.access.csv 也带 BOM | 跨平台一致性问题;CSV header 解析失败 |
| **1.3** | 🔴 P0 | `test_odoo_model.py` 结构损坏:重复 import 3 次、`test_15` 缺闭合、2 个同名 `TestGoldImprint` | 整个测试文件从未真正运行过 |
| **1.4** | 🟡 P1 | `_create_batch()` 写 `available_weight_g` (compute 字段)+ 绕过 `action_available` 校验 | 账实不符 + 状态机不一致 |
| **1.5** | 🔴 P0 | `gold.workorder.report` 默认 `state="confirmed"` + `create()` 内自动扣减批次 | UI 草稿态不扣、API 默认扣,**业务语义不一致**;草稿改数后确认会双花 |

---

## 🔧 主要改动

### Commit 1: BOM 清理 (`7820a73`)

```diff
- 7 files: controllers (5) + report (1) + scripts (1) + CSV (1)
+ 纯 BOM (EF BB BF) → UTF-8,7 行改动
```

### Commit 2: CI + validate (`b2c170a`)

**`.github/workflows/ci.yml`** — 路径修正:
```yaml
- run: python scripts/validate_dunhuang_gold_mes.py
+ run: python scripts/validate_dunhuanggold_workshop_mes.py

- pyflakes addons/dunhuang_gold_mes/...
+ pyflakes addons/dunhuanggold_workshop_mes/...
```

**`scripts/validate_dunhuanggold_workshop_mes.py`** — 跨平台 + CSV header 检测:
```python
# 1. 强制 UTF-8 输出,兼容 Windows GBK
sys.stdout.reconfigure(encoding="utf-8")
# 2. 用 ASCII 符号 ([OK]/[FAIL]) 替代 ✓ ✗

# 3. CSV header 检测修复:支持逗号/Tab/分号三种分隔符
csv_lines = [line for line in ...
    if line.strip() and not (line.startswith("id,") or
                              line.startswith("id\t") or
                              line.startswith("id;"))]
```

### Commit 3: 模型状态机重构 (`44b02d0`)

**`gold_finished_goods._create_batch()`**:
```python
# 修复前:绕过状态机 + 写 compute 字段
batch = self.env["gold.material.batch"].create({...})
batch.write({"state": "available"})  # 绕过 action_available

# 修复后:走正常状态机路径
batch = self.env["gold.material.batch"].create({..., "state": "draft"})
batch.action_available()  # 触发 inspection / net_weight 校验
```

**`gold.workorder.report` 状态机**:
```python
# 修复前:create() 内自动扣批次(默认 state="confirmed")
state = fields.Selection(default="confirmed", ...)  # 永远立即扣减

# 修复后:create() 只做填充,confirm() 显式触发副作用
state = fields.Selection(default="draft", ...)
def action_confirm(self):
    """显式确认才扣减批次/启动生产/累计模具"""
    if rec.input_batch_id:
        rec.input_batch_id.consume(rec.input_weight_g)
    if rec.production_id and rec.production_id.gold_state == "confirmed":
        rec.production_id.action_start()
    if rec.production_id and rec.production_id.gold_mold_id:
        rec.production_id.gold_mold_id.action_add_usage(rec.output_piece_count)
    rec.state = "confirmed"

def action_cancel(self):
    """已确认报工作废不回退(避免双花)"""
```

**`controllers/mes_api.py`** — 同步 API 行为:
```python
rec = request.env["gold.workorder.report"].create({...})
# 默认走完整流程,UI 草稿场景可传 confirm=false
if data.get("confirm", True):
    rec.action_confirm()
```

### Commit 4: 测试文件重写 (`4a020a9`)

- 顶部统一 import,删除 6 处重复
- 修复 `test_15` 缺闭合的 for 循环
- 合并 2 个同名 `TestGoldImprint`
- 26 个测试方法结构清晰
- 增加辅助方法 `_make_batch` / `_report` / `_users` / `_partner`,测试间相互独立

---

## ✅ 验证结果

### validate 脚本(跨平台)
```
============================================================
  [OK] Python 语法          (35 模型 + 5 controller)
  [OK] XML 格式             (38 个 xml 文件)
  [OK] manifest data        (全部 data 文件存在)
  [OK] access CSV           (109 条权限记录)
  [OK] menu action          (全部引用解析)

[PASS] 全部检查通过
```

### 算法测试
```
Ran 35 tests in 0.001s OK  (ExitCode: 0)
```

### 模型测试(需 Odoo 环境)
```bash
odoo-bin -d test_db -i dunhuanggold_workshop_mes \
    --test-enable --test-tags=dunhuanggold_workshop_mes \
    --stop-after-init
```
预期: 26 测试全部通过(原文件 0 个能跑,现 26 个)

---

## 📝 兼容性影响

| 组件 | 兼容性 |
|------|--------|
| 旧 UI 草稿态创建的报工 | ✅ **不变**(本来就 draft → 草稿写一遍更显式) |
| 旧 API 调用 `POST /workorder_report`(不传 confirm) | ✅ **行为等价**:旧 = 立即 confirmed+扣减 / 新 = 默认 confirm=true 也立即 confirmed+扣减 |
| 旧 API 显式传 `confirm=false` | 🆕 保留草稿态供编辑 |
| DB schema | ✅ **零变更**(纯 Python 逻辑调整) |
| XML / views | ✅ **零变更** |

---

## 🚫 不在本次范围内

- Phase 2:性能索引 / API 限流 / 审计日志 / 多 record rule
- Phase 3:addon 拆分 / 边缘网关 / 时序库 / 件级 WIP
- Phase 4:AI 视觉 / 区块链 / React 前端 / K8s

完整计划见 [`docs/MES-IMPROVEMENT-REFERENCE-2026-08-16.md`](docs/MES-IMPROVEMENT-REFERENCE-2026-08-16.md) 和 [`docs/CODE-QUALITY-UPGRADE-ROADMAP-2026-08-16.md`](docs/CODE-QUALITY-UPGRADE-ROADMAP-2026-08-16.md)。

---

## 🔗 相关 Issue / 参考

- 自评文档:`docs/CODE-QUALITY-UPGRADE-ROADMAP-2026-08-16.md` P0-1 / P0-3
- 改进参考:`docs/MES-IMPROVEMENT-REFERENCE-2026-08-16.md` §五 实现度评估

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
