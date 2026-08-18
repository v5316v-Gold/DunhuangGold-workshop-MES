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

// ============ Phase 3: 生产订单 ============
const productions = [
  { id: 1, name: 'MO-00425', product: '古法金素圈戒指', process_type: 'oil_press', qty: 100, gold_state: 'in_progress', received_at: '2026-08-05 08:30', current_workstation: 'WS-OWP' },
  { id: 2, name: 'MO-00422', product: '18K金钻石戒指', process_type: 'lost_wax', qty: 50, gold_state: 'in_progress', received_at: '2026-08-05 09:00', current_workstation: 'WS-LWC' },
  { id: 3, name: 'MO-00430', product: '足金手镯', process_type: 'oil_press', qty: 30, gold_state: 'received', received_at: '2026-08-05 10:00', current_workstation: null },
];

// ============ Phase 3: 工序交接卡 ============
const flowCards = [
  { id: 1, name: 'FC20260805-00001', sn: 'GLD-20260805-RING-001', in_operation: 'OWP03 落料', in_workstation: 'WS-OWP-01', sender: '李四', receiver: '王五', handover_time: '2026-08-05 09:15', weight_in_g: 5.250, weight_out_g: 5.235, state: 'completed' },
  { id: 2, name: 'FC20260805-00002', sn: 'GLD-20260805-RING-001', in_operation: 'OWP04 油压成形', in_workstation: 'WS-OWP-02', sender: '王五', receiver: '张三', handover_time: '2026-08-05 09:50', weight_in_g: 5.235, weight_out_g: 5.180, state: 'completed' },
  { id: 3, name: 'FC20260805-00003', sn: 'GLD-20260805-RING-001', in_operation: 'OWP06 执模', in_workstation: 'WS-OWP-04', sender: '张三', receiver: '张三', handover_time: '2026-08-05 10:25', weight_in_g: 5.180, weight_out_g: null, state: 'at_station' },
];

// ============ Phase 3.2: NCR 不合格品处理单 ============
const ncrs = [
  { id: 1, name: 'NCR20260805-00001', ncr_time: '2026-08-05 10:35', source: 'workorder_report', defect_type: '划痕', defect_description: '执模工序发现表面划痕', production_name: 'MO-00425', piece_sn: 'GLD-20260805-RING-003', defect_weight_g: 5.18, disposition: 'rework', disposition_time: '2026-08-05 10:50', disposition_by: '班组长-菩提老祖', estimated_loss_amount: 0.0 },
  { id: 2, name: 'NCR20260805-00002', ncr_time: '2026-08-05 11:15', source: 'xrf', defect_type: '含量不足', defect_description: 'XRF 检测金含量 99.42% < 标准 99.50%', production_name: 'MO-00422', piece_sn: 'GLD-20260805-DIA-007', defect_weight_g: 8.30, disposition: 'pending', estimated_loss_amount: 250.0 },
];

// ============ Phase 3.3: 包装 ============
const packages = [
  { id: 1, name: 'PKG20260805-00001', package_no: 'PKG20260805-00001', package_kind: 'box', package_time: '2026-08-05 14:30', production_name: 'MO-00425', piece_count: 10, total_weight_g: 51.8, total_value: 30184.0, ngtc_cert_no: 'NGTC-2026-000123', state: 'sealed', sealed_time: '2026-08-05 14:35' },
];

// ============ Phase 3.2 增强: 损耗监控预警 (3 层) ============
const lossAlerts = [
  // Layer 1: 工序级(操作员张三执模损耗过大)
  { id: 1, name: 'LA20260805-00001', alert_type: 'operation', severity: 'warning', status: 'open',
    triggered_at: '2026-08-05 10:25:00',
    workorder_report_id: 2, production_id: 1, operation_id: 6, operator_id: 1,
    actual_loss_g: 0.115, expected_loss_g: 0.040,
    actual_loss_rate: 2.20, expected_loss_rate: 0.76, deviation_pct: 1.44,
    description: '工序 OWP06 执模 损耗 2.20% (定额 0.76%, 偏差 +1.44%)',
    suggestion: '建议检查: 1) 操作员张三资质 2) 设备精度 3) 模具磨损' },
  // Layer 1: 工序级(红色-超过 1g 绝对偏差)
  { id: 2, name: 'LA20260805-00002', alert_type: 'operation', severity: 'danger', status: 'open',
    triggered_at: '2026-08-05 11:42:00',
    workorder_report_id: 4, production_id: 2, operation_id: 8, operator_id: 2,
    actual_loss_g: 1.250, expected_loss_g: 0.500,
    actual_loss_rate: 12.50, expected_loss_rate: 5.00, deviation_pct: 7.50,
    description: '工序 OWP08 印记 损耗 12.50% (定额 5.00%, 偏差 +7.50%) 🔴 严重',
    suggestion: '🔴 严重: 偏差 > 50% + 绝对值 > 1g, 自动建 NCR 待处置' },
  // Layer 2: 累积级(MO-00422 总损耗超定额)
  { id: 3, name: 'LA20260805-00003', alert_type: 'cumulative', severity: 'danger', status: 'acknowledged',
    triggered_at: '2026-08-05 12:10:00',
    production_id: 2,
    cumulative_loss_g: 4.85, cumulative_standard_g: 3.50,
    actual_loss_rate: 13.86, expected_loss_rate: 10.00,
    description: '生产订单 MO-00422 累积损耗 4.85g 超定额 3.50g',
    acknowledged_at: '2026-08-05 12:30:00', acknowledged_by_id: 3,
    suggestion: '订单总损耗超定额,需班组长/主任 review 工艺与每道工序' },
  // Layer 3: 趋势级(操作员王五 Z-Score > 3)
  { id: 4, name: 'LA20260805-00004', alert_type: 'trend', severity: 'warning', status: 'open',
    triggered_at: '2026-08-05 22:00:00',
    operator_id: 2,
    actual_loss_rate: 5.20, baseline_avg: 3.50, baseline_std: 0.45, z_score: 3.78,
    description: 'Z-Score = 3.78 (超过 3σ 阈值)',
    suggestion: '操作员 王五 过去 30 天平均 3.50% 标准差 0.45, 当前 5.20% 偏离 Z=3.78' },
  // Layer 3: 趋势级(设备 OBP-001 异常)
  { id: 5, name: 'LA20260805-00005', alert_type: 'trend', severity: 'danger', status: 'open',
    triggered_at: '2026-08-05 22:00:00',
    equipment_id: 1,
    actual_loss_rate: 6.80, baseline_avg: 2.80, baseline_std: 0.60, z_score: 6.67,
    description: 'Z-Score = 6.67 (超过 5σ 严重)',
    suggestion: '设备 OBP-001 过去 30 天平均 2.80% 标准差 0.60, 当前 6.80% 偏离 Z=6.67 🔴 设备需校准' },
  // 已解决
  { id: 6, name: 'LA20260804-00001', alert_type: 'operation', severity: 'warning', status: 'resolved',
    triggered_at: '2026-08-04 14:30:00',
    workorder_report_id: 1, production_id: 1, operation_id: 5, operator_id: 1,
    actual_loss_g: 0.080, expected_loss_g: 0.060,
    actual_loss_rate: 1.50, expected_loss_rate: 1.13, deviation_pct: 0.37,
    description: '工序 OWP05 切边 损耗 1.50% (定额 1.13%, 偏差 +0.37%)',
    resolved_at: '2026-08-04 15:00:00', resolved_by_id: 3,
    resolve_note: '已查实为操作员首次操作不熟练,指导后已正常' },
];

const db = {
  batches, equipment, workorderReports,
  environmentSensors, environmentReadings,
  hazardousChemicals, maintenanceOrders, spareParts,
  inventoryCounts, finishedGoods, materialReturns,
  certificates, attendance, energyMeters, sops, ecns,
  productions, flowCards, ncrs, packages, lossAlerts,
  nextId, computeKpi,
};

module.exports = db;
