# DunhuangGold-workshop-MES — 数据模型

## 一、模型清单(35 个主模型, 覆盖「人机料法环 + 生产后」)

| 模型 | 中文名 | 关键字段 | 要素 |
|------|--------|---------|------|
| `gold.measurement` | 计量单位 | code, factor_to_gram, category | 料 |
| `gold.process.operation` | 工艺工序 | code, process_type, standard_time_hours, standard_loss_rate | 法 |
| `gold.process.route` | 工艺路线模板 | code, process_type, variant, total_loss_rate | 法 |
| `gold.process.route.line` | 工艺路线明细 | route_id, operation_id, sequence | 法 |
| `gold.workstation` | 工位 | code, workstation_type, process_type, equipment_ids | 机 |
| `gold.equipment` | 设备台账 | code, category, protocol, oee | 机 |
| `gold.material.batch` | 金料批次 | batch_no, gold_purity, net_weight_g, current_price | 料 |
| `gold.price.engine` | 实时金价 | price_time, gold_type, price_close | 料 |
| `gold.recycle` | 旧金回收 | partner_id, final_purity, valuation_amount | 料 |
| `gold.mold` | 模具 | code, mold_type, rated_life_count, used_count | 法 |
| `gold.mold.maintenance` | 模具保养 | mold_id, date, description | 法 |
| `gold.wax.model` | 蜡模 | code, origin, weight_g, state | 法 |
| `gold.workorder.report` | 工序报工 | production_id, input_weight_g, output_weight_g, loss_rate | 法 |
| `gold.loss.trace` | 损耗追溯 | trace_time, loss_diff_pct, review_status | 法 |
| `gold.quality.inspection` | 质检 | weight_g, purity_pct, imprint_passed, result | 料 |
| `gold.imprint` | 印记 | material_code, purity_code, factory_code, ocr_verified | 料 |
| `gold.xrf.record` | XRF 检测 | gold_pct, platinum_pct, main_metal_pct | 料 |
| `gold.dashboard` | 看板(KPI) | (auto=False, 纯计算) | 全局 |
| `gold.employee.certificate` | 员工资质证书 | cert_type, holder_id, expiry_date, is_valid | 人 |
| `gold.work.attendance` | 考勤/工时 | employee_id, shift_date, check_in, work_hours | 人 |
| `gold.maintenance.order` | 设备维护工单 | equipment_id, maintenance_type, state, cost | 机 |
| `gold.spare.part` | 备品备件 | code, stock_qty, min_stock_qty, is_low_stock | 机 |
| `gold.sop.document` | SOP 作业指导书 | operation_id, version, document_type, state | 法 |
| `gold.ecn` | 工程变更单 | change_type, route_id, bom_id, state | 法 |
| `gold.environment.sensor` | 环境传感器 | sensor_type, alarm_min, alarm_max, protocol | 环 |
| `gold.environment.reading` | 环境读数 | sensor_id, value, state, alarm_desc | 环 |
| `gold.hazardous.chemical` | 危化品台账 | category, danger_level, lock_required, stock_qty | 环 |
| `gold.hazardous.chemical.usage` | 危化品领用 | chemical_id, qty, requester_id, dual_custody_confirmed | 环 |
| `gold.energy.meter` | 能源计量表 | energy_type, meter_level, rate_price | 环 |
| `gold.energy.reading` | 能耗读数 | meter_id, cumulative_value, period_consumption | 环 |
| `gold.inventory.count` | 金料盘点单 | inventory_date, counter_id, total_diff_g, state | 生产后 |
| `gold.inventory.count.line` | 盘点明细 | batch_id, book_weight_g, actual_weight_g, diff_g | 生产后 |
| `gold.finished.goods` | 成品入库单 | post_date, total_piece_count, generate_batch, state | 生产后 |
| `gold.finished.goods.line` | 成品入库明细 | piece_id, actual_weight_g | 生产后 |
| `gold.material.return` | 班后回料单 | return_source, weight_g, create_new_batch, state | 生产后 |

## 二、扩展关系

```
mrp.production  ←extends  gold_process_type / gold_route_id / gold_state / gold_actual_weight_g
mrp.workorder    ←extends  gold_process_operation_id / gold_standard_loss_rate
mrp.bom          ←extends  gold_process_type / gold_route_id / gold_standard_weight_g
mrp.routing      ←extends  gold_process_type / gold_route_template_id
product.template ←extends  gold_purity / gold_imprint_code / gold_process_type / gold_route_id
product.category ←extends  gold_metal_type / gold_purity / gold_imprint_code
res.company      ←extends  gold_factory_code / gold_loss_tolerance_pct / gold_xrf_min_pct
```

## 三、关键字段精度

| 字段 | 类型 | 精度 | 说明 |
|------|------|------|------|
| 重量 | Float | digits=(18,6) | 0.001g 精度 |
| 价格 | Float | digits=(18,4) | 0.0001 元/g |
| 含量 | Float | digits=(6,4) | 0.0001% |
| 损耗率 | Float | digits=(6,4) | 0.0001% |
| 工时 | Float | digits=(10,4) | 0.0001 小时 |
| 金额 | Float | digits=(18,2) | 0.01 元 |

## 四、状态机

### 金料批次
```
draft → available → locked → depleted
   ↓        ↓
  scrap ← scrap
```

### 旧金回收
```
draft → inspecting → quoted → confirmed → refining → done
                                                              ↓
                                                        cancelled
```

### 模具
```
new → in_use → scrapped
       ↓
       idle ⇄ maintenance
```

### 蜡模
```
draft → stock → in_tree → casted
   ↓       ↓
  scrap ← scrap
```

### 印记
```
draft → confirmed → (三级分离: operator / reviewer / encoder)
                  → ocr_verified
```

### 维护工单 (机)
```
draft → planned → in_progress → done
                    ↓
                 cancelled
```

### SOP 作业指导书 (法)
```
draft → effective → obsolete
```

### ECN 工程变更 (法)
```
draft → review → approved → effective
   ↓        ↓
rejected ← rejected
```

### 危化品领用 (环)
```
draft → confirmed
   ↓
cancelled
```

### 环境读数 (环)
```
normal ⇄ alarm  (由阈值自动判定)
```

### 资质证书 (人)
```
is_valid = (expiry_date >= today)  (自动计算)
```

### 金料盘点单 (生产后)
```
draft → counting → reviewed → posted
  ↓
cancelled
```

### 成品入库单 (生产后)
```
draft → posted
  ↓
cancelled
```

### 班后回料单 (生产后)
```
draft → confirmed
  ↓
cancelled
```

## 五、损耗率叠加公式

```
工艺路线总损耗率 = 1 - Π(1 - li/100)
其中 li 为各工序定额损耗率

示例: 油压 9 道,各道损耗率 0.5%、1.5%、1.5%、4%、1.5%、0、0、0、0
       总损耗率 = 1 - (1-0.005)*(1-0.015)*(1-0.015)*(1-0.04)*(1-0.015)
                  = 1 - 0.995*0.985*0.985*0.96*0.985
                  = 1 - 0.9119
                  = 8.81%
```

## 六、关键业务规则

1. **金料批次不可拆分**:每个批次独立管理,跨批次需新建批次
2. **重量平衡**:`net_weight_g = available + allocated + consumed`,差异 > 0.005g 报错
3. **印记三级分离**:操作员 / 复核员 / 编码员,任何人不可兼任
4. **XRF 周期**:每批抽样,合格即过;不合格触发复检
5. **超耗预警**:工序 `|实际-定额| > 阈值(默认 20%)` 触发预警
6. **模具寿命**:`剩余 ≤ 额定 × 寿命预警阈值(默认 10%)` 触发预警
7. **资质有效性 (人)**:`expiry_date >= today` 为有效,过期自动 `is_valid=False`(作业指导书: 资质过期自动停工)
8. **危化品双人双锁 (环)**:高毒/剧毒危化品 `lock_required` 时,领用必须 `dual_custody_confirmed`,且保管员与领用人不可同一人
9. **环境超限 (环)**:读数超过传感器 `alarm_min/alarm_max` 阈值自动置 `alarm` 状态(约定: 阈值 ≤ 0 视为不启用该边界)
10. **备件低库存 (机)**:`stock_qty < min_stock_qty` 自动置 `is_low_stock`
11. **SOP 版本唯一 (法)**:`code + version` 唯一,变更走 ECN 审批流
12. **盘点差异回写 (生产后)**:盘点过账时 `diff = 实盘 - 账面` 回写批次净重与可用重量(盘亏超可用拦截, 复核人与盘点人需分离)
13. **成品入库 (生产后)**:件级 SN 由 `finished → stored`, 可选生成成品批次(source=finished_goods), 要求同款物料
14. **班后回料 (生产后)**:新建回料批次(source=return) 或回入现有批次(调用 `batch.receive`), 可关联报工同步回收重量

## 七、人机料法环要素覆盖对照

| 要素 | 现有模型 | 本次新增/增强 |
|------|----------|----------------|
| 人 Man | 7 个 RBAC 角色 | 资质证书矩阵 + 考勤/工时 + 资质有效期自动校验 |
| 机 Machine | gold.equipment + OEE + device API | 维护工单(PM/CM/BM) + 备品备件 + 低库存预警 |
| 料 Material | 金料批次 + 金价 + 回收 + BOM | (已较强, 保持) |
| 法 Method | 工序 + 工艺路线 + 模具 + 蜡模 | SOP 作业指导书(版本化) + ECN 工程变更审批流 |
| 环 Environment | (缺失) | 环境监测(温湿度/洁净度/照度/噪声/VOC/PM2.5) + 危化品双人双锁 + 能耗分项计量 |
| 生产后 | 批次锁定 + 重量平衡(仅有底子) | 金料盘点单(盘盈盘亏回写) + 成品入库单(件级 SN 入库) + 班后回料单 |
