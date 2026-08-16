# DunhuangGold-workshop-MES

> **Dunhuang Gold Workshop MES**: oil-press stamping + lost-wax casting, purpose-built for precious-metal jewelry (Au / K-gold / Pt / Ag / stone setting) with full **4M1E (Man / Machine / Material / Method / Environment)** coverage + post-production closed loop.

> Dedicated MES-ERP for precious metal jewelry workshops — Internal version 17.0.1.1.0
> Focus: **oil-press stamping + lost-wax casting** with 0.001g gold material tracking.
> Full **4M1E (Man/Machine/Material/Method/Environment)** coverage + post-production closed loop.

[![CI](https://github.com/v5316v-Gold/Dunhuang-workshop-ERP/workflows/CI/badge.svg)](https://github.com/v5316v-Gold/Dunhuang-workshop-ERP/actions)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Odoo](https://img.shields.io/badge/Odoo-17.0-714B67)](https://www.odoo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791)](https://www.postgresql.org)

**English** | [中文](README.zh-CN.md)


## Why This Project?

A precious metal jewelry workshop has unique ERP requirements that generic systems fail to handle:

| Standard ERP | DunhuangGold-workshop-MES |
|---|---|
| Generic inventory | **Gold batch** with 0.001g precision, Au/Pt/Pd purity, **real-time gold price** |
| Manufacturing | **Oil-press 9-step + Lost-wax 11-step** dual routes with **per-step loss rate** |
| Quality | **GB 11887-2012 §4.1 mark** (material + purity + factory + assay) with **3-person separation** |
| Sales | **Per-piece SN** (one gold ring = one unique SN) + **NGTC certificate** + scan-to-verify |
| Counterfeit | **XRF GB/T 18043-2013** content detection with spec report |

## Tech Stack

- **Framework**: Odoo 17.0 CE (open source)
- **Backend**: Python 3.11
- **Database**: PostgreSQL 15 (NUMERIC 18,6 for gram precision)
- **API**: REST / JSON (27 endpoints, MES-friendly)
- **Frontend**: QWeb + OWL 2 + JavaScript
- **Reports**: QWeb + wkhtmltopdf (PDF)
- **Equipment Protocol**: OPC UA / MQTT / Modbus / RS-232 (reserved interface)
- **Deployment**: Docker / docker-compose / systemd / nginx

## Features

### 1. Process Master Data
- **Oil-press 9 steps**: Design → Blanking → Oil-press → Trim → Setting → Polish → Mark → QC
- **Lost-wax 11 steps**: Design → Master → Wax → Tree → Investment → Cast → Knockout → Set → Polish → Mark → QC
- **Process routes**: 3 templates (OWP_STD / LWC_STD / LWC_SIMPLE) with auto-calculated cumulative loss rate

### 2. Gold Material & Pricing
- **Gold batch**: 0.001g precision (NUMERIC 18,6), full lifecycle (draft → available → locked → depleted)
- **Real-time gold price**: SGE / LBMA / Bank / API push
- **Price locking**: 15min / 30min / 1h / today for order quotation
- **Old gold recycle**: Customer KYC + XRF + fire test + AML threshold

### 3. Production Execution
- **Multi-level BOM**: Gold material + cast stones + packaging + solder
- **Workorder report**: Electronic balance auto-capture (NUMERIC 18,6)
- **Loss traceability**: Process-level tracking + diff% threshold warning
- **Mold lifecycle**: Rated life + auto-warning + auto-scrap

### 4. Quality & Marking
- **4-axis QC**: Weight / Purity / Mark / Surface
- **XRF content**: GB/T 18043-2013 standard, multi-metal analysis
- **Mark**: GB 11887-2012 §4.1 mandatory compliance with **3-person separation** (operator / reviewer / encoder)
- **OCR verification**: Mark text auto-recognition

### 5. Per-Piece SN (One Item One Code)
- **Global unique SN**: `GLD-YYYYMMDD-STYLECODE-SEQ`
- **QR code**: Auto-generated, scan-to-verify
- **NGTC cert**: National Gemstone & Jade Quality Supervision & Inspection Center linkage

### 6. MES REST API
27 endpoints for workshop terminals / mobile apps:
```
POST /dunhuang_gold_mes/api/v1/login
POST /dunhuang_gold_mes/api/v1/workorder_report      # Electronic balance → report
POST /dunhuang_gold_mes/api/v1/price/push           # SGE / LBMA gold price push
POST /dunhuang_gold_mes/api/v1/imprint/verify       # OCR mark check
POST /dunhuang_gold_mes/api/v1/device/heartbeat     # Equipment OEE + status
GET  /dunhuang_gold_mes/api/v1/dashboard/kpi        # Big-screen KPI
POST /dunhuang_gold_mes/api/v1/environment/reading  # Env sensor reading (4M1E)
POST /dunhuang_gold_mes/api/v1/hazchem/issue        # Hazardous chemical dual-custody issue
POST /dunhuang_gold_mes/api/v1/energy/reading       # Energy meter reading
POST /dunhuang_gold_mes/api/v1/maintenance/order    # Maintenance order
GET  /dunhuang_gold_mes/api/v1/certificate/verify   # Employee certificate check
POST /dunhuang_gold_mes/api/v1/inventory/count      # Inventory count (post-production)
POST /dunhuang_gold_mes/api/v1/finished_goods/post  # Finished goods receipt by SN
POST /dunhuang_gold_mes/api/v1/material_return/confirm  # Material return
```

### 7. Workshop Dashboard
- Daily production / In-progress / Over-loss warning / Mold warning
- Process distribution (oil-press vs lost-wax)
- 7-day loss trend
- Gold price + inventory valuation

### 8. 4M1E Full Coverage
- **Man**: Employee certificate matrix + attendance/work-hours + auto expiry check
- **Machine**: Equipment ledger + OEE + maintenance orders (PM/CM/BM) + spare parts (low-stock alert)
- **Material**: Gold batch (0.001g) + price engine + recycle + multi-level BOM + weight balance check
- **Method**: Process routes + molds/wax + versioned SOP + ECN engineering change approval flow
- **Environment**: Sensors (temp/humidity/cleanliness/lux/noise/VOC/PM2.5 with threshold alarm) + hazardous chemical dual-custody + energy metering

### 9. Post-Production Closed Loop
- **Inventory count**: Book vs actual weight + surplus/shortage + review approval + auto write-back to batch (shortage over available is blocked)
- **Finished goods receipt**: Per-piece SN `finished → stored` + optional finished-goods batch
- **Material return**: Gate/scrap/polish-powder back to vault (new batch or merge into existing via `batch.receive`)

## Installation

### Quick (Docker)
```bash
git clone https://github.com/v5316v-Gold/Dunhuang-workshop-ERP.git
cd Dunhuang-workshop-ERP
docker-compose up -d
# Open http://localhost:8069
# admin / admin (set in .env)
```

### Standard (Odoo)
```bash
# 1. Copy module
cp -r addons/dunhuang_gold_mes /path/to/odoo/addons/

# 2. Validate
python scripts/validate_dunhuang_gold_mes.py

# 3. Install
odoo-bin -d mydb -i dunhuang_gold_mes --addons-path=/path/to/addons --stop-after-init

# 4. Start
odoo-bin -d mydb
```

### Physical Machine (systemd)
See [deploy/README.md](deploy/README.md).

## Validation

```bash
# 5 checks all green
python scripts/validate_dunhuang_gold_mes.py

# 35 unit tests all pass
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Roadmap

- [x] v17.0.1.0.0 (2026-08-05): Core modules + tests + deployment
- [x] v17.0.1.1.0: 4M1E full coverage (Man/Machine/Method/Environment) + post-production closed loop + offline UI preview
- [ ] v17.0.2.0.0: NGTC one-cert-one-code API
- [ ] v17.1.0.0.0: OPC UA device adapter demo
- [ ] v18.0.0.0.0: AI visual quality inspection

See [CHANGELOG.md](CHANGELOG.md) for full history.

## Documentation

- [docs/QUICKSTART.md](docs/QUICKSTART.md) — 5-minute quick start
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md) — 35 data models (4M1E + post-production) + ER diagram
- [docs/API.md](docs/API.md) — 27 REST endpoints
- [docs/QUICKSTART.md](docs/QUICKSTART.md) — Deployment guide
- [CHANGELOG.md](CHANGELOG.md) — Version history

## License

Apache-2.0 (or LGPL-3, your choice). See [LICENSE](LICENSE).

## Compliance

- `GB 11887-2012` Marks on precious metal jewelry
- `GB/T 18043-2013` XRF detection
- `QB/T 1689-2010` Precious metal jewelry terminology
- Gold VAT instant-refund (Caishui [2002] 142, [2008] 171, [2010] 51)
- Anti-Money Laundering (AML)

## Note

中文 README 见 [README.zh-CN.md](README.zh-CN.md) (项目同时维护中英双语).
