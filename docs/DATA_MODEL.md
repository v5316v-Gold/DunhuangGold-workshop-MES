# 贵金属车间 ERP — 数据模型

## 一、模型清单(18 个主模型)

| 模型 | 中文名 | 关键字段 |
|------|--------|---------|
| `gold.measurement` | 计量单位 | code, factor_to_gram, category |
| `gold.process.operation` | 工艺工序 | code, process_type, standard_time_hours, standard_loss_rate |
| `gold.process.route` | 工艺路线模板 | code, process_type, variant, total_loss_rate |
| `gold.process.route.line` | 工艺路线明细 | route_id, operation_id, sequence |
| `gold.workstation` | 工位 | code, workstation_type, process_type, equipment_ids |
| `gold.equipment` | 设备台账 | code, category, protocol, oee |
| `gold.material.batch` | 金料批次 | batch_no, gold_purity, net_weight_g, current_price |
| `gold.price.engine` | 实时金价 | price_time, gold_type, price_close |
| `gold.recycle` | 旧金回收 | partner_id, final_purity, valuation_amount |
| `gold.mold` | 模具 | code, mold_type, rated_life_count, used_count |
| `gold.mold.maintenance` | 模具保养 | mold_id, date, description |
| `gold.wax.model` | 蜡模 | code, origin, weight_g, state |
| `gold.workorder.report` | 工序报工 | production_id, input_weight_g, output_weight_g, loss_rate |
| `gold.loss.trace` | 损耗追溯 | trace_time, loss_diff_pct, review_status |
| `gold.quality.inspection` | 质检 | weight_g, purity_pct, imprint_passed, result |
| `gold.imprint` | 印记 | material_code, purity_code, factory_code, ocr_verified |
| `gold.xrf.record` | XRF 检测 | gold_pct, platinum_pct, main_metal_pct |
| `gold.dashboard` | 看板(KPI) | (auto=False, 纯计算) |

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
