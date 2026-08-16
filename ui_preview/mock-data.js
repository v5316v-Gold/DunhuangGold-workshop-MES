// 敦煌金 ERP - Mock 数据层 (内存存储)
// 模拟 Odoo 后端数据, 结构对齐 REST API 返回字段 (snake_case)
// 前端通过 /api/* 读写这里的数据

let _seq = 1000;
function nextId() { return ++_seq; }

// ============ 金料批次 ============
const batches = [
  { id: 1, batch_no: "GL20260805-00001", product: "足金 9999 板料", purity: 99.99, net_weight_g: 5000.000, available_weight_g: 5000.000, allocated_weight_g: 0, consumed_weight_g: 0, source: "supplier", current_price: 582.50, current_value: 2912500.00, inspection_state: "passed", state: "available" },
  { id: 2, batch_no: "GL20260805-00002", product: "足金 9999 板料", purity: 99.99, net_weight_g: 3200.000, available_weight_g: 2800.000, allocated_weight_g: 0, consumed_weight_g: 400.000, source: "supplier", current_price: 582.50, current_value: 1631000.00, inspection_state: "passed", state: "available" },
  { id: 3, batch_no: "GL20260805-00003", product: "18K 金 板料", purity: 75.00, net_weight_g: 2000.000, available_weight_g: 1500.000, allocated_weight_g: 0, consumed_weight_g: 500.000, source: "supplier", current_price: 442.00, current_value: 663000.00, inspection_state: "passed", state: "available" },
  { id: 4, batch_no: "GL20260804-00005", product: "PT950 铂金 板料", purity: 95.00, net_weight_g: 800.000, available_weight_g: 798.000, allocated_weight_g: 0, consumed_weight_g: 2.000, source: "supplier", current_price: 320.00, current_value: 255360.00, inspection_state: "passed", state: "available" },
  { id: 5, batch_no: "HS20260801-00001", product: "回收料", purity: 99.50, net_weight_g: 350.500, available_weight_g: 350.500, allocated_weight_g: 0, consumed_weight_g: 0, source: "recycle", current_price: 570.85, current_value: 200083.43, inspection_state: "passed", state: "available" },
  { id: 6, batch_no: "GL20260803-00002", product: "足金 9999 板料", purity: 99.99, net_weight_g: 2500.000, available_weight_g: 0, allocated_weight_g: 0, consumed_weight_g: 2500.000, source: "supplier", current_price: 582.50, current_value: 0, inspection_state: "passed", state: "depleted" },
];

// ============ 设备 ============
const equipment = [
  { id: 1, code: "OBP-001", name: "油压机", category: "oil_press_machine", process_type: "oil_press", state: "running", protocol: "modbus_tcp", ip: "192.168.1.11", oee: 92.5, next_calibration_date: "2026-09-01" },
  { id: 2, code: "MLF-002", name: "熔金炉", category: "melting_furnace", process_type: "lost_wax", state: "maintenance", protocol: "opc_ua", ip: "192.168.1.12", oee: 78.0, next_calibration_date: "2026-08-20" },
  { id: 3, code: "LMK-001", name: "激光打字机", category: "laser_marker", process_type: "common", state: "running", protocol: "mtconnect", ip: "192.168.1.13", oee: 96.0, next_calibration_date: "2026-10-01" },
  { id: 4, code: "BAL-001", name: "电子天平", category: "balance", process_type: "common", state: "idle", protocol: "rs232", ip: "192.168.1.20", oee: 0, next_calibration_date: "2026-08-15" },
];

// ============ 工序报工 ============
const workorderReports = [
  { id: 1, name: "BG20260805-00015", production: "MO-00425", operation: "OWP06 执模", workstation: "WS-OWP", operator: "张三", input_weight_g: 5.250, output_weight_g: 5.180, loss_g: 0.070, loss_rate: 1.33, standard_loss_rate: 4.00, quality_state: "passed", report_time: "2026-08-05 06:28" },
  { id: 2, name: "BG20260805-00014", production: "MO-00422", operation: "LWC06 熔金浇铸", workstation: "WS-LWC", operator: "李四", input_weight_g: 120.000, output_weight_g: 105.000, loss_g: 15.000, loss_rate: 12.50, standard_loss_rate: 10.00, quality_state: "failed", report_time: "2026-08-05 05:45" },
  { id: 3, name: "BG20260805-00013", production: "MO-00420", operation: "OWP04 油压成形", workstation: "WS-OWP", operator: "王五", input_weight_g: 5.500, output_weight_g: 5.420, loss_g: 0.080, loss_rate: 1.45, standard_loss_rate: 1.50, quality_state: "passed", report_time: "2026-08-05 05:30" },
  { id: 4, name: "BG20260805-00012", production: "MO-00418", operation: "OWP07 抛光", workstation: "WS-FIN", operator: "赵六", input_weight_g: 5.420, output_weight_g: 5.330, loss_g: 0.090, loss_rate: 1.66, standard_loss_rate: 1.50, quality_state: "passed", report_time: "2026-08-05 04:50" },
  { id: 5, name: "BG20260805-00011", production: "MO-00412", operation: "LWC08 执模", workstation: "WS-FIN", operator: "钱七", input_weight_g: 5.000, output_weight_g: 4.650, loss_g: 0.350, loss_rate: 7.00, standard_loss_rate: 5.00, quality_state: "rework", report_time: "2026-08-05 04:15" },
];

// ============ 环境 ============
const environmentSensors = [
  { id: 1, code: "ENV-TEMP-01", name: "电镀车间温度传感器", sensor_type: "temperature", unit: "℃", location_desc: "电镀车间", alarm_min: 15.0, alarm_max: 35.0 },
  { id: 2, code: "ENV-HUM-01", name: "电镀车间湿度传感器", sensor_type: "humidity", unit: "%RH", location_desc: "电镀车间", alarm_min: 30.0, alarm_max: 80.0 },
  { id: 3, code: "ENV-VOC-01", name: "电镀车间 VOC 传感器", sensor_type: "voc", unit: "ppm", location_desc: "电镀车间", alarm_min: 0.0, alarm_max: 0.3 },
  { id: 4, code: "ENV-CLN-01", name: "钻石房洁净度传感器", sensor_type: "cleanliness", unit: "级", location_desc: "钻石房", alarm_min: 0.0, alarm_max: 7.0 },
  { id: 5, code: "ENV-NSE-01", name: "抛光车间噪声传感器", sensor_type: "noise", unit: "dB", location_desc: "抛光车间", alarm_min: 0.0, alarm_max: 75.0 },
  { id: 6, code: "ENV-PM25-01", name: "抛光车间 PM2.5 传感器", sensor_type: "pm25", unit: "mg/m³", location_desc: "抛光车间", alarm_min: 0.0, alarm_max: 0.5 },
];
const environmentReadings = [
  { id: 1, sensor_code: "ENV-TEMP-01", sensor_name: "电镀车间温度传感器", sensor_type: "temperature", value: 24.6, unit: "℃", state: "normal", alarm_desc: "", reading_time: "2026-08-05 18:20" },
  { id: 2, sensor_code: "ENV-HUM-01", sensor_name: "电镀车间湿度传感器", sensor_type: "humidity", value: 52.0, unit: "%RH", state: "normal", alarm_desc: "", reading_time: "2026-08-05 18:20" },
  { id: 3, sensor_code: "ENV-VOC-01", sensor_name: "电镀车间 VOC 传感器", sensor_type: "voc", value: 0.35, unit: "ppm", state: "alarm", alarm_desc: "超过上限 0.300 ppm", reading_time: "2026-08-05 18:19" },
  { id: 4, sensor_code: "ENV-CLN-01", sensor_name: "钻石房洁净度传感器", sensor_type: "cleanliness", value: 6, unit: "级", state: "normal", alarm_desc: "", reading_time: "2026-08-05 18:15" },
  { id: 5, sensor_code: "ENV-NSE-01", sensor_name: "抛光车间噪声传感器", sensor_type: "noise", value: 68.0, unit: "dB", state: "normal", alarm_desc: "", reading_time: "2026-08-05 18:15" },
  { id: 6, sensor_code: "ENV-PM25-01", sensor_name: "抛光车间 PM2.5 传感器", sensor_type: "pm25", value: 0.42, unit: "mg/m³", state: "normal", alarm_desc: "", reading_time: "2026-08-05 18:15" },
];

// ============ 危化品 ============
const hazardousChemicals = [
  { id: 1, code: "HC-GOLD-CN", name: "氰化金钾 (KAu(CN)2)", cas_no: "13967-50-5", category: "cyanide", danger_level: "high", lock_required: true, storage_location: "危化品柜 A-01", stock_qty: 500.0, stock_unit: "g", safety_stock: 100.0 },
  { id: 2, code: "HC-AG-CN", name: "氰化银钾 (KAg(CN)2)", cas_no: "506-61-6", category: "cyanide", danger_level: "high", lock_required: true, storage_location: "危化品柜 A-01", stock_qty: 200.0, stock_unit: "g", safety_stock: 50.0 },
  { id: 3, code: "HC-HCL", name: "盐酸 (HCl)", cas_no: "7647-01-0", category: "acid", danger_level: "medium", lock_required: true, storage_location: "危化品柜 B-02", stock_qty: 6.0, stock_unit: "L", safety_stock: 5.0 },
  { id: 4, code: "HC-HNO3", name: "硝酸 (HNO3)", cas_no: "7697-37-2", category: "acid", danger_level: "medium", lock_required: true, storage_location: "危化品柜 B-02", stock_qty: 4.0, stock_unit: "L", safety_stock: 5.0 },
];

// ============ 维护工单 / 备件 ============
const maintenanceOrders = [
  { id: 1, name: "WX20260805-00003", equipment: "油压机 OBP-001", maintenance_type: "bm", priority: "3", state: "in_progress", assignee: "孙师傅", planned_date: "2026-08-05", duration_hours: 1.5, maintenance_cost: 320.00 },
  { id: 2, name: "WX20260805-00002", equipment: "熔金炉 MLF-002", maintenance_type: "cm", priority: "2", state: "in_progress", assignee: "周师傅", planned_date: "2026-08-05", duration_hours: 0.8, maintenance_cost: 150.00 },
  { id: 3, name: "WX20260804-00006", equipment: "激光打字机 LMK-001", maintenance_type: "pm", priority: "1", state: "planned", assignee: "孙师傅", planned_date: "2026-08-08", duration_hours: null, maintenance_cost: null },
  { id: 4, name: "WX20260804-00005", equipment: "电子天平 BAL-001", maintenance_type: "pm", priority: "1", state: "done", assignee: "周师傅", planned_date: "2026-08-04", duration_hours: 1.0, maintenance_cost: 0.00 },
];
const spareParts = [
  { id: 1, code: "SP-OBP-001", name: "油压机冲头", category: "模具件", equipment: "油压机 OBP-001", stock_qty: 2, min_stock_qty: 5, unit: "件", is_low_stock: true, supplier: "东莞精工" },
  { id: 2, code: "SP-LMK-003", name: "激光器镜片", category: "光学件", equipment: "激光打字机", stock_qty: 12, min_stock_qty: 4, unit: "件", is_low_stock: false, supplier: "深圳光电" },
  { id: 3, code: "SP-MLF-002", name: "熔金炉坩埚", category: "耐材", equipment: "熔金炉 MLF-002", stock_qty: 3, min_stock_qty: 6, unit: "件", is_low_stock: true, supplier: "洛阳耐材" },
  { id: 4, code: "SP-BAL-001", name: "天平防风罩", category: "配件", equipment: "电子天平", stock_qty: 8, min_stock_qty: 2, unit: "件", is_low_stock: false, supplier: "梅特勒" },
];

// ============ 盘点 / 成品入库 / 回料 ============
const inventoryCounts = [
  {
    id: 1, name: "PD20260805-00001", inventory_date: "2026-08-05", state: "counting", counter: "张三", reviewer: null,
    total_book_weight_g: 10550.500, total_actual_weight_g: 10549.300, total_diff_g: -1.200,
    lines: [
      { batch_no: "GL20260805-00001", product: "足金 9999 板料", book_weight_g: 5000.000, actual_weight_g: 5000.000, diff_g: 0.000, result: "平账" },
      { batch_no: "GL20260805-00002", product: "足金 9999 板料", book_weight_g: 3200.000, actual_weight_g: 3199.500, diff_g: -0.500, result: "盘亏" },
      { batch_no: "GL20260805-00003", product: "18K 金 板料", book_weight_g: 2000.000, actual_weight_g: 1999.300, diff_g: -0.700, result: "盘亏" },
      { batch_no: "HS20260801-00001", product: "回收料", book_weight_g: 350.500, actual_weight_g: 350.500, diff_g: 0.000, result: "平账" },
    ],
  },
];
const finishedGoods = [
  {
    id: 1, name: "CP20260805-00003", post_date: "2026-08-05", state: "posted", generate_batch: false, total_piece_count: 4, total_weight_g: 22.640,
    lines: [
      { sn: "GLD-20260805-RING-0001", style: "18K 钻石戒指", purity: "Au750", weight_g: 5.180, imprint: "合格", qc: "通过", ngtc: "NGTC-88231", state: "已入库" },
      { sn: "GLD-20260805-RING-0002", style: "18K 钻石戒指", purity: "Au750", weight_g: 5.160, imprint: "合格", qc: "通过", ngtc: "NGTC-88232", state: "已入库" },
      { sn: "GLD-20260805-PEND-0011", style: "足金 9999 吊坠", purity: "Au9999", weight_g: 3.880, imprint: "合格", qc: "通过", ngtc: "NGTC-88240", state: "已入库" },
      { sn: "GLD-20260805-BRAC-0007", style: "PT950 铂金手链", purity: "Pt950", weight_g: 8.420, imprint: "合格", qc: "通过", ngtc: "NGTC-88244", state: "已入库" },
    ],
  },
];
const materialReturns = [
  { id: 1, name: "HL20260805-00006", return_date: "2026-08-05", return_source: "gate", material_type: "gold", product: "足金 9999", weight_g: 1.250, target: "新批次 HL-0001", report: "BG...00014", state: "confirmed" },
  { id: 2, name: "HL20260805-00005", return_date: "2026-08-05", return_source: "scrap_edge", material_type: "gold", product: "18K 金", weight_g: 0.800, target: "回入 GL...00003", report: "BG...00012", state: "confirmed" },
  { id: 3, name: "HL20260805-00004", return_date: "2026-08-05", return_source: "polish_powder", material_type: "gold", product: "足金 9999", weight_g: 1.200, target: "新批次 HL-0002", report: "BG...00010", state: "confirmed" },
  { id: 4, name: "HL20260805-00003", return_date: "2026-08-05", return_source: "gate", material_type: "wax", product: "—", weight_g: 3.100, target: "蜡模回收", report: "BG...00008", state: "draft" },
];

// ============ 人: 资质 / 考勤 ============
const certificates = [
  { id: 1, name: "熔金操作证", cert_no: "CERT-M-0032", cert_type: "melting", cert_level: "senior", holder: "张三", issue_date: "2024-01-15", expiry_date: "2027-01-15", days_to_expire: 525, is_valid: true },
  { id: 2, name: "镶石技能等级", cert_no: "CERT-S-0018", cert_type: "stone_setting", cert_level: "technician", holder: "李四", issue_date: "2023-06-01", expiry_date: "2026-06-01", days_to_expire: 300, is_valid: true },
  { id: 3, name: "危化品操作证", cert_no: "CERT-E-0007", cert_type: "electroplating", cert_level: "intermediate", holder: "王五", issue_date: "2022-09-10", expiry_date: "2026-09-10", days_to_expire: 26, is_valid: true },
  { id: 4, name: "首饰检验员证", cert_no: "CERT-I-0002", cert_type: "inspector", cert_level: "senior", holder: "赵六", issue_date: "2021-03-20", expiry_date: "2025-03-20", days_to_expire: -30, is_valid: false },
];
const attendance = [
  { id: 1, employee: "张三", shift_type: "day", workstation: "油压工位", check_in: "08:00", check_out: "17:00", work_hours: 8.0, report_count: 8, output_weight_g: 41.250, attendance_state: "normal" },
  { id: 2, employee: "李四", shift_type: "day", workstation: "精加工工位", check_in: "08:12", check_out: "17:00", work_hours: 7.8, report_count: 6, output_weight_g: 30.800, attendance_state: "late" },
  { id: 3, employee: "王五", shift_type: "night", workstation: "铸造工位", check_in: "20:00", check_out: "04:00", work_hours: 8.0, report_count: 5, output_weight_g: 22.100, attendance_state: "normal" },
  { id: 4, employee: "赵六", shift_type: "day", workstation: "质检工位", check_in: "—", check_out: "—", work_hours: 0.0, report_count: 0, output_weight_g: 0.000, attendance_state: "absent" },
];

// ============ 能耗 ============
const energyMeters = [
  { id: 1, code: "ELEC-01", name: "车间总电表", energy_type: "electricity", meter_level: "workshop", cumulative_value: 12345.6, period_consumption: 1240.0, period_amount: 868.00, unit: "kWh" },
  { id: 2, code: "GAS-01", name: "熔金炉燃气表", energy_type: "gas", meter_level: "equipment", cumulative_value: 3210.8, period_consumption: 36.5, period_amount: 143.00, unit: "m³" },
  { id: 3, code: "AIR-01", name: "空压机气表", energy_type: "compressed_air", meter_level: "equipment", cumulative_value: 8990.0, period_consumption: 210.0, period_amount: 63.00, unit: "m³" },
];

// ============ 法: SOP / ECN ============
const sops = [
  { id: 1, code: "SOP-OWP06", name: "执模作业指导书", operation: "OWP06 执模", version: "V2.1", document_type: "pdf", state: "effective", effective_date: "2026-06-01", review_date: "2027-06-01", author: "张三" },
  { id: 2, code: "SOP-LWC06", name: "熔金浇铸作业指导书", operation: "LWC06 熔金浇铸", version: "V1.0", document_type: "video", state: "effective", effective_date: "2026-05-15", review_date: "2027-05-15", author: "李四" },
  { id: 3, code: "SOP-OWP07", name: "抛光作业指导书", operation: "OWP07 抛光", version: "V1.2", document_type: "pdf", state: "draft", effective_date: null, review_date: null, author: "王五" },
];
const ecns = [
  { id: 1, name: "ECN20260805-00001", title: "油压执模损耗定额 4%→3.5%", change_type: "routing", state: "review", route: "RT-OWP-STD", bom: null, proposed_by: "张三", approved_by: null, effective_date: null },
  { id: 2, name: "ECN20260804-00004", title: "18K 镶石款焊料替换", change_type: "bom", state: "approved", route: null, bom: "BOM-RING-18K", proposed_by: "李四", approved_by: "王主任", effective_date: "2026-08-10" },
  { id: 3, name: "ECN20260803-00003", title: "熔金温度曲线优化", change_type: "sop", state: "effective", route: "RT-LWC-STD", bom: null, proposed_by: "王五", approved_by: "王主任", effective_date: "2026-08-05" },
];

// ============ 看板 KPI ============
function computeKpi() {
  return {
    today: "2026-08-05",
    done_today: 28,
    in_progress: 5,
    over_loss_count: 1,
    critical_mold_count: 2,
    oil_press_orders: 3,
    lost_wax_orders: 2,
    current_gold_price: 582.50,
    total_value: 5661943.43,
    avg_loss_rate: 3.85,
    xrf_count_today: 20,
    xrf_passed_pct: 98.5,
  };
}

const db = {
  batches, equipment, workorderReports,
  environmentSensors, environmentReadings,
  hazardousChemicals, maintenanceOrders, spareParts,
  inventoryCounts, finishedGoods, materialReturns,
  certificates, attendance, energyMeters, sops, ecns,
  nextId, computeKpi,
};

module.exports = db;
