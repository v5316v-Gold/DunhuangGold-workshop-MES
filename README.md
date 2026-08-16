# DunhuangGold-workshop-MES

> **Dunhuang Gold Workshop MES**: oil-press stamping + lost-wax casting, purpose-built for precious-metal jewelry (Au / K-gold / Pt / Ag / stone setting) with full **4M1E (Man / Machine / Material / Method / Environment)** coverage + post-production closed loop.

[![CI](https://github.com/v5316v-Gold/DunhuangGold-workshop-MES/workflows/CI/badge.svg)](https://github.com/v5316v-Gold/DunhuangGold-workshop-MES/actions)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Odoo](https://img.shields.io/badge/Odoo-17.0-714B67)](https://www.odoo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791)](https://www.postgresql.org)

**📖 [English full README](README.en.md)** | **[中文完整 README](README.zh-CN.md)**

---

## What is it

**DunhuangGold-workshop-MES** is a deeply-customized **Odoo 17 CE** Manufacturing Execution System for precious-metal jewelry workshops. It focuses on **oil-press stamping** and **lost-wax casting** dual routes, supporting **0.001g gold material precision**, per-piece one-thing-one-code SN, equipment OEE, hazardous chemical dual-custody, and other industry-specific requirements.

## Pain points solved

Generic ERP / MES struggles in precious-metal jewelry:

| Pain point | Solution |
|---|---|
| Gold gram precision insufficient (typical: 0.1g) | **NUMERIC(18,6)** 0.001g precision + weight balance check (delta > 0.005g raises error) |
| Real-time gold price volatility, hard to lock quotes | **Gold price engine** SGE/LBMA/Bank/API push + price lock 15min/30min/1h/today |
| GB 11887-2012 mark mandatory compliance | **Mark 3-person separation** operator/reviewer/encoder + OCR verification |
| Per-piece traceability (one ring = one item) | **Per-piece SN** one-thing-one-code + NGTC certificate + scan-to-verify |
| Loss standard vs actual deviation hard to control | **Workorder report** balance auto-capture + auto loss-rate + threshold alert (default 20%) |
| Oil-press 9-step + lost-wax 11-step dual routes | **Multi-level BOM** + process route template + process-level gold cost |
| Hazardous chemicals (KAu(CN)2) dual-custody | **Hazchem ledger** + 3-person segregation + stock deduction |
| Mold lifecycle | **Usage accumulation + alert + auto-scrap** |
| Old-gold recycling + AML | **Customer KYC + XRF/fire test + large-amount auto-flag** (≥ 50k) |

## System architecture

```
+------------------------+     +---------------------------+
|     Station PDA/Tablet |     |   Workshop big-screen     |
|  (scan / weight / btn)  |     |   (KPI / process mix)      |
+----------+-------------+     +-------------+-------------+
           | REST API (27 endpoints)                   |
+----------v----------------------------------------v----+
|             Odoo 17 HTTP Controllers                   |
+----------------------------+--------------------------+
|   Man   |  Machine  |  Method  |  Environment          |
|  cert/  |  maint/   |  SOP/    |  hazchem/             |
|  attend |  spare    |  ECN     |  energy               |
|         Material + Post-production (count/recv/return)|
+----------------------------------+----------------------+
                                     | protocol adapters
+----------------------------------v----------------------+
|   Equipment layer (furnace / press / balance / laser)    |
|   OPC UA / MQTT / Modbus / RS-232 / RS-485              |
+---------------------------------------------------------+
```

## Quick start (5 min)

```bash
# 1. Clone
git clone https://github.com/v5316v-Gold/DunhuangGold-workshop-MES.git
cd DunhuangGold-workshop-MES

# 2. Auto-validate (no Odoo needed)
python scripts/validate_dunhuanggold_workshop_mes.py

# 3. Install into Odoo 17
cp -r addons/dunhuanggold_workshop_mes /path/to/odoo/addons/
odoo-bin -d mydb -i dunhuanggold_workshop_mes --addons-path=/path/to/addons --stop-after-init

# 4. Try the front-end UI preview (no Odoo)
cd ui_preview
node server.js
# → http://localhost:8080
```

## Documentation

### README
- **English** (full): [README.en.md](README.en.md)
- **中文** (完整): [README.zh-CN.md](README.zh-CN.md)

### Core docs
- **Quick start** — [docs/QUICKSTART.md](docs/QUICKSTART.md) (5-min start)
- **Data model** — [docs/DATA_MODEL.md](docs/DATA_MODEL.md) (35 models, 4M1E + post-production)
- **REST API** — [docs/API.md](docs/API.md) (27 endpoints)
- **Frontend architecture** — [ui_preview/ARCHITECTURE.md](ui_preview/ARCHITECTURE.md) (dynamic UI preview)
- **Deploy** — [deploy/README.md](deploy/README.md) (Docker / systemd)
- **Changelog** — [CHANGELOG.md](CHANGELOG.md)

## Scope

- **In scope**: raw material receiving → production → QC → finished goods storage
- **Out of scope (downstream systems)**: sales / finance / retail (interfaces reserved)

## License

Apache-2.0 (or LGPL-3, your choice). See [LICENSE](LICENSE).
