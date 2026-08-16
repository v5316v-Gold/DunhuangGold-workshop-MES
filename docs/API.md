# REST API — DunhuangGold-workshop-MES

## 端点列表

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/dunhuang_gold_mes/api/v1/login` | 工位登录 |
| GET  | `/dunhuang_gold_mes/api/v1/production/{id}` | 获取生产订单详情 |
| GET  | `/dunhuang_gold_mes/api/v1/workorder/by_station/{station_id}` | 工位待执行工单 |
| POST | `/dunhuang_gold_mes/api/v1/workorder_report` | 工序报工(天平直采) |
| GET  | `/dunhuang_gold_mes/api/v1/batch/{batch_no}` | 查询金料批次 |
| POST | `/dunhuang_gold_mes/api/v1/batch/allocate` | 分配批次重量 |
| GET  | `/dunhuang_gold_mes/api/v1/price/current` | 当前金价 |
| POST | `/dunhuang_gold_mes/api/v1/price/push` | 推送金价 |
| POST | `/dunhuang_gold_mes/api/v1/imprint/verify` | 印记 OCR 校验 |
| POST | `/dunhuang_gold_mes/api/v1/xrf/save` | XRF 检测结果 |
| GET  | `/dunhuang_gold_mes/api/v1/dashboard/kpi` | 看板 KPI |
| POST | `/dunhuang_gold_mes/api/v1/device/heartbeat` | 设备心跳 |
| POST | `/dunhuang_gold_mes/api/v1/device/metric` | 设备度量上报 |
| GET  | `/dunhuang_gold_mes/api/v1/device/list` | 设备列表 |
| POST | `/dunhuang_gold_mes/api/v1/environment/reading` | 环境读数上报 (环) |
| GET  | `/dunhuang_gold_mes/api/v1/environment/latest` | 最新环境读数 (环) |
| GET  | `/dunhuang_gold_mes/api/v1/environment/alarms` | 环境超限报警 (环) |
| GET  | `/dunhuang_gold_mes/api/v1/hazchem/list` | 危化品台账列表 (环) |
| POST | `/dunhuang_gold_mes/api/v1/hazchem/issue` | 危化品领用 (环) |
| POST | `/dunhuang_gold_mes/api/v1/energy/reading` | 能耗读数上报 (环) |
| POST | `/dunhuang_gold_mes/api/v1/maintenance/order` | 维护工单上报 (机) |
| GET  | `/dunhuang_gold_mes/api/v1/maintenance/list` | 维护工单列表 (机) |
| GET  | `/dunhuang_gold_mes/api/v1/certificate/verify` | 人员资质校验 (人) |
| POST | `/dunhuang_gold_mes/api/v1/inventory/count` | 创建金料盘点单 (生产后) |
| GET  | `/dunhuang_gold_mes/api/v1/inventory/list` | 盘点单列表 (生产后) |
| POST | `/dunhuang_gold_mes/api/v1/finished_goods/post` | 成品入库-按件级 SN (生产后) |
| POST | `/dunhuang_gold_mes/api/v1/material_return/confirm` | 班后回料 (生产后) |

## 通用返回格式

```json
{
  "ok": true,
  "msg": "ok",
  "data": { ... }
}
```

错误:
```json
{
  "ok": false,
  "error": "错误信息"
}
```

## 1. 登录

```bash
POST /dunhuang_gold_mes/api/v1/login
Content-Type: application/json

{
  "login": "工位操作员",
  "password": "***"
}
```

返回:
```json
{
  "ok": true,
  "data": {
    "uid": 8,
    "name": "张三",
    "groups": ["车间班组长"]
  }
}
```

## 2. 工序报工(MES 工位核心)

```bash
POST /dunhuang_gold_mes/api/v1/workorder_report
Content-Type: application/json
Cookie: session_id=xxx

{
  "production_id": 42,
  "operation_id": 6,
  "workorder_id": 87,
  "workstation_id": 3,
  "equipment_id": 1,
  "operator_id": 8,
  "input_batch_id": 12,
  "input_weight_g": 5.250,
  "output_weight_g": 5.180,
  "output_piece_count": 1,
  "work_hours": 0.45,
  "start_time": "2026-08-05T10:00:00Z",
  "end_time": "2026-08-05T10:27:00Z",
  "source": "balance",
  "balance_id": 2,
  "quality_state": "passed"
}
```

返回:
```json
{
  "ok": true,
  "data": {
    "id": 100,
    "name": "BG20260805-00001",
    "loss_g": 0.070,
    "loss_rate": 1.3333,
    "loss_diff_pct": -0.1667,
    "is_over_loss": false,
    "trace_id": 95
  }
}
```

## 3. 当前金价

```bash
GET /dunhuang_gold_mes/api/v1/price/current?gold_type=au9999&source=sge
```

```json
{
  "ok": true,
  "data": {
    "gold_type": "au9999",
    "source": "sge",
    "price": 582.5,
    "timestamp": "2026-08-05T10:30:00"
  }
}
```

## 4. 看板 KPI

```bash
GET /dunhuang_gold_mes/api/v1/dashboard/kpi
```

```json
{
  "ok": true,
  "data": {
    "today": "2026-08-05",
    "done_today": 12,
    "in_progress": 5,
    "over_loss_count": 1,
    "critical_mold_count": 2,
    "oil_press_orders": 3,
    "lost_wax_orders": 2,
    "current_gold_price": 582.5
  }
}
```

## 5. 设备心跳

```bash
POST /dunhuang_gold_mes/api/v1/device/heartbeat
Content-Type: application/json

{
  "device_code": "OBP-001",
  "state": "running",
  "runtime_hours": 152.5,
  "downtime_hours": 8.2,
  "total_count": 1234,
  "good_count": 1210
}
```

## 6. 设备度量上报(电子天平直采)

```bash
POST /dunhuang_gold_mes/api/v1/device/metric
Content-Type: application/json

{
  "device_code": "BAL-001",
  "metrics": {
    "weight_g": 5.182
  },
  "context": {
    "workorder_id": 87
  }
}
```

## 7. 印记 OCR 校验

```bash
POST /dunhuang_gold_mes/api/v1/imprint/verify
Content-Type: application/json

{
  "imprint_id": 23,
  "expected": "Au 9999 XX"
}
```

```json
{
  "ok": true,
  "data": {
    "id": 23,
    "verified": true,
    "mismatch": false,
    "content": "Au 9999 XX",
    "passed": true
  }
}
```

## 8. XRF 检测结果

```bash
POST /dunhuang_gold_mes/api/v1/xrf/save
Content-Type: application/json

{
  "production_id": 42,
  "product_id": 5,
  "operator_id": 8,
  "gold_pct": 99.987,
  "copper_pct": 0.005,
  "zinc_pct": 0.003,
  "standard_pct": 99.50
}
```

```json
{
  "ok": true,
  "data": {
    "id": 56,
    "is_passed": true,
    "main_metal_pct": 99.987
  }
}
```

## 9. 环境读数上报 (环)

```bash
POST /dunhuang_gold_mes/api/v1/environment/reading
Content-Type: application/json

{
  "sensor_code": "ENV-TEMP-01",
  "value": 28.5,
  "reading_time": "2026-08-05T10:30:00Z"
}
```

```json
{ "ok": true, "data": { "id": 1, "state": "normal", "alarm_desc": "" } }
```

## 10. 危化品领用 (环, 双人双锁)

```bash
POST /dunhuang_gold_mes/api/v1/hazchem/issue
Content-Type: application/json

{
  "chemical_code": "HC-GOLD-CN",
  "qty": 10.0,
  "usage_type": "issue",
  "dual_custody_confirmed": true,
  "confirm": true
}
```

```json
{ "ok": true, "data": { "id": 3, "name": "WH...", "state": "confirmed" } }
```

## 11. 能耗读数上报 (环)

```bash
POST /dunhuang_gold_mes/api/v1/energy/reading
Content-Type: application/json

{ "meter_code": "ELEC-01", "cumulative_value": 12345.6 }
```

```json
{ "ok": true, "data": { "id": 1, "period_consumption": 120.5, "period_amount": 96.4 } }
```

## 12. 维护工单上报 (机)

```bash
POST /dunhuang_gold_mes/api/v1/maintenance/order
Content-Type: application/json

{ "equipment_code": "OBP-001", "maintenance_type": "cm", "priority": "2", "description": "异响" }
```

## 13. 人员资质校验 (人)

```bash
GET /dunhuang_gold_mes/api/v1/certificate/verify?user_id=8&cert_type=melting
```

```json
{
  "ok": true,
  "data": {
    "user_id": 8,
    "cert_type": "melting",
    "qualified": true,
    "certificates": [{ "name": "熔金操作证", "expiry_date": "2027-01-01", "days_to_expire": 140 }]
  }
}
```

## 14. 金料盘点 (生产后)

```bash
POST /dunhuang_gold_mes/api/v1/inventory/count
Content-Type: application/json

{
  "location_id": 1,
  "lines": [
    { "batch_id": 12, "actual_weight_g": 5.250 },
    { "batch_id": 15, "actual_weight_g": 3.108 }
  ],
  "start": true
}
```

```json
{ "ok": true, "data": { "id": 1, "name": "PD...", "state": "counting", "total_diff_g": -0.012 } }
```

## 15. 成品入库 (生产后, 按件级 SN)

```bash
POST /dunhuang_gold_mes/api/v1/finished_goods/post
Content-Type: application/json

{ "piece_sns": ["GLD-20260805-RING-0001", "GLD-20260805-RING-0002"], "generate_batch": false }
```

```json
{ "ok": true, "data": { "id": 2, "name": "CP...", "state": "posted", "total_piece_count": 2, "total_weight_g": 11.200 } }
```

## 16. 班后回料 (生产后)

```bash
POST /dunhuang_gold_mes/api/v1/material_return/confirm
Content-Type: application/json

{ "product_id": 5, "weight_g": 1.230, "return_source": "gate", "create_new_batch": true }
```

```json
{ "ok": true, "data": { "id": 3, "name": "HL...", "state": "confirmed", "batch_id": 20 } }
```

## 错误码

| HTTP 状态 | 含义 |
|----------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 404 | 资源不存在 |
| 500 | 系统错误 |

## 鉴权

- `auth="user"`: 通过 Odoo session 鉴权
- `auth="public"`: 公开接口,需内置 token(参考 SGE/LBMA 推送)
- CSRF: POST 请求可设置 `csrf=False`(已配置)

## 设备协议

设计上预留:
- OPC UA: 通过外部服务转 JSON
- MQTT: 通过 EMQX 等桥接
- Modbus: 通过 Edge Gateway 转 JSON
- RS-232: 通过串口服务器转 JSON
- 电子天平: 直采(如梅特勒 XPR 系列)
