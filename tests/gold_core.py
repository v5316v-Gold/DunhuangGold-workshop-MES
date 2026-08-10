"""
敦煌金加工车间 ERP — 核心算法(纯 Python POC)
=========================================

【依据】Odoo 模型中关键算法的"无框架"实现,可在离线环境下运行 + 单元测试。

包含:
  - 计量单位换算
  - 损耗率叠加公式
  - 单件金料成本计算
  - 旧金回收估价
  - 金价锁价
  - 模具寿命预警
  - 金料批次重量平衡
  - 超耗预警判定
  - SN 编码生成
  - 委外加工
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict


# ============== 计量单位 ==============

@dataclass
class Measurement:
    """贵金属计量单位"""
    code: str
    name: str
    factor_to_gram: float

    def to_gram(self, qty: float) -> float:
        return qty * self.factor_to_gram

    def from_gram(self, gram: float) -> float:
        return gram / self.factor_to_gram


GRAM = Measurement("g", "克", 1.0)
MILLIGRAM = Measurement("mg", "毫克", 0.001)
KILOGRAM = Measurement("kg", "千克", 1000.0)
TROY_OUNCE = Measurement("oz", "金衡盎司", 31.1034768)
QIAN = Measurement("qian", "钱", 3.75)
LIANG = Measurement("liang", "两", 37.5)
CARAT = Measurement("ct", "克拉", 0.2)


# ============== 工艺工序 ==============

@dataclass
class ProcessOperation:
    code: str
    name: str
    standard_time_hours: float
    standard_loss_rate: float
    equipment_category: str = ""
    returnable_gold: bool = False
    returnable_wax: bool = False


OIL_PRESS_OPS = [
    ProcessOperation("OWP01", "设计开模", 6.0, 0.0),
    ProcessOperation("OWP02", "备料", 0.5, 0.0),
    ProcessOperation("OWP03", "落料", 0.2, 0.5),
    ProcessOperation("OWP04", "油压成形", 0.3, 1.5),
    ProcessOperation("OWP05", "切边 / 修边", 0.3, 1.5),
    ProcessOperation("OWP06", "执模", 0.75, 4.0),
    ProcessOperation("OWP07", "抛光", 0.4, 1.5),
    ProcessOperation("OWP08", "印记", 0.1, 0.0),
    ProcessOperation("OWP09", "检验入库", 0.12, 0.0),
]

LOST_WAX_OPS = [
    ProcessOperation("LWC01", "设计", 6.0, 0.0),
    ProcessOperation("LWC02", "起版", 3.0, 0.0),
    ProcessOperation("LWC03", "雕蜡 / 3D 打印", 0.75, 1.5, returnable_wax=True),
    ProcessOperation("LWC04", "树", 0.3, 0.0),
    ProcessOperation("LWC05", "灌石膏 / 脱蜡 / 焙烧", 6.0, 0.0),
    ProcessOperation("LWC06", "熔金浇铸", 0.75, 10.0, returnable_gold=True),
    ProcessOperation("LWC07", "冲石膏 / 拆树", 0.3, 0.5),
    ProcessOperation("LWC08", "执模", 1.0, 5.0),
    ProcessOperation("LWC09", "镶石(可选)", 1.0, 1.0),
    ProcessOperation("LWC10", "抛光", 0.4, 1.5),
    ProcessOperation("LWC11", "印记 / 检验入库", 0.15, 0.0),
]


# ============== 损耗率叠加公式 ==============

def calculate_total_loss_rate(operations: List[ProcessOperation]) -> float:
    """工艺路线总损耗率 = 1 - Π(1 - li/100)"""
    compound = 1.0
    for op in operations:
        compound *= (1 - op.standard_loss_rate / 100.0)
    return (1 - compound) * 100


def calculate_total_time(operations: List[ProcessOperation]) -> float:
    return sum(op.standard_time_hours for op in operations)


# ============== 单件金料成本 ==============

def calculate_gold_cost(
    finished_weight_g: float,
    total_loss_rate: float,
    current_price: float,
    processing_fee: float = 0.0,
    stone_cost: float = 0.0,
    plating_cost: float = 0.0,
    packaging_cost: float = 0.0,
    detection_cost: float = 0.0,
    design_cost: float = 0.0,
    profit_margin: float = 0.0,
) -> Dict:
    gold_cost = finished_weight_g * (1 + total_loss_rate / 100.0) * current_price
    total_cost = (
        gold_cost + processing_fee + stone_cost + plating_cost +
        packaging_cost + detection_cost + design_cost
    )
    total_with_profit = total_cost * (1 + profit_margin / 100.0)
    return {
        "gold_cost": round(gold_cost, 2),
        "processing_fee": processing_fee,
        "stone_cost": stone_cost,
        "plating_cost": plating_cost,
        "packaging_cost": packaging_cost,
        "detection_cost": detection_cost,
        "design_cost": design_cost,
        "total_cost": round(total_cost, 2),
        "with_profit": round(total_with_profit, 2),
        "profit_margin": profit_margin,
    }


# ============== 旧金回收 ==============

def calculate_recycle_valuation(
    net_weight_g: float,
    purity_pct: float,
    current_price: float,
    discount_factor: float = 0.97,
) -> Dict:
    if not 0 <= purity_pct <= 100:
        raise ValueError(f"含量必须在 0-100,实际: {purity_pct}")
    if not 0 <= discount_factor <= 1:
        raise ValueError(f"折价系数必须在 0-1,实际: {discount_factor}")
    pure_g = net_weight_g * (purity_pct / 100.0)
    valuation = pure_g * current_price * discount_factor
    return {
        "pure_g": round(pure_g, 6),
        "valuation": round(valuation, 2),
        "discount_factor": discount_factor,
        "current_price": current_price,
    }


def is_large_amount(valuation: float, threshold: float = 50000.0) -> bool:
    return valuation >= threshold


# ============== 金价锁价 ==============

@dataclass
class PriceLock:
    price: float
    lock_time: datetime
    lock_until: datetime
    gold_type: str = "au9999"
    source: str = "sge"

    def is_expired(self, now: datetime = None) -> bool:
        if now is None:
            now = datetime.now()
        return now >= self.lock_until

    def remaining_minutes(self, now: datetime = None) -> float:
        if now is None:
            now = datetime.now()
        if self.lock_until <= now:
            return 0.0
        return (self.lock_until - now).total_seconds() / 60.0


def lock_price(
    current_price: float,
    gold_type: str = "au9999",
    lock_minutes: int = 30,
    source: str = "sge",
) -> PriceLock:
    now = datetime.now()
    return PriceLock(
        price=current_price,
        lock_time=now,
        lock_until=now + timedelta(minutes=lock_minutes),
        gold_type=gold_type,
        source=source,
    )


# ============== 模具寿命预警 ==============

@dataclass
class Mold:
    code: str
    name: str
    rated_life_count: int
    used_count: int = 0
    warning_threshold_pct: float = 10.0

    @property
    def remaining_count(self) -> int:
        return max(0, self.rated_life_count - self.used_count)

    @property
    def remaining_pct(self) -> float:
        if self.rated_life_count <= 0:
            return 0.0
        return (self.remaining_count / self.rated_life_count) * 100

    def is_critical(self) -> bool:
        return self.remaining_pct <= self.warning_threshold_pct

    def is_scrapped(self) -> bool:
        return self.used_count >= self.rated_life_count


# ============== 金料批次重量平衡 ==============

@dataclass
class MaterialBatch:
    batch_no: str
    net_weight_g: float
    available_weight_g: float = 0.0
    allocated_weight_g: float = 0.0
    consumed_weight_g: float = 0.0

    def __post_init__(self):
        if self.available_weight_g == 0.0:
            self.available_weight_g = self.net_weight_g

    def allocate(self, weight_g: float) -> bool:
        if weight_g > self.available_weight_g:
            raise ValueError(
                f"批次 {self.batch_no} 可用重量不足:申请 {weight_g:.3f}g,可用 {self.available_weight_g:.3f}g"
            )
        self.allocated_weight_g += weight_g
        self.available_weight_g -= weight_g
        return True

    def consume(self, weight_g: float) -> bool:
        if weight_g > self.allocated_weight_g:
            raise ValueError(
                f"批次 {self.batch_no} 分配不足:消耗 {weight_g:.3f}g,已分配 {self.allocated_weight_g:.3f}g"
            )
        self.allocated_weight_g -= weight_g
        self.consumed_weight_g += weight_g
        return True

    def release(self, weight_g: float) -> bool:
        if weight_g > self.allocated_weight_g:
            raise ValueError(
                f"批次 {self.batch_no} 释放超分配:{weight_g:.3f}g > {self.allocated_weight_g:.3f}g"
            )
        self.allocated_weight_g -= weight_g
        self.available_weight_g += weight_g
        return True

    def is_balanced(self, tolerance: float = 0.005) -> bool:
        total = self.available_weight_g + self.allocated_weight_g + self.consumed_weight_g
        return abs(self.net_weight_g - total) <= tolerance


# ============== 超耗预警 ==============

@dataclass
class WorkorderReport:
    operation_code: str
    input_weight_g: float
    output_weight_g: float
    standard_loss_rate: float
    tolerance_pct: float = 20.0

    @property
    def loss_g(self) -> float:
        return max(0.0, self.input_weight_g - self.output_weight_g)

    @property
    def loss_rate(self) -> float:
        if self.input_weight_g <= 0:
            return 0.0
        return (self.loss_g / self.input_weight_g) * 100

    @property
    def loss_diff_pct(self) -> float:
        return self.loss_rate - self.standard_loss_rate

    def is_over_loss(self) -> bool:
        return abs(self.loss_diff_pct) > self.tolerance_pct


# ============== 件级 SN 编码 ==============

@dataclass
class PieceSN:
    sn: str
    product_code: str
    production_id: int
    qr_payload: str = ""

    def __post_init__(self):
        if not self.qr_payload:
            self.qr_payload = f"https://verify.dunhuang-gold-mes.com/piece/{self.sn}"

    @staticmethod
    def generate(product_code: str, production_id: int, seq: int, date: datetime = None) -> str:
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y%m%d")
        return f"GLD-{date_str}-{product_code}-{seq:05d}"


# ============== 委外加工 ==============

@dataclass
class OutsourceOrder:
    partner: str
    outgoing_weight_g: float
    incoming_weight_g: float
    processing_fee: float
    current_gold_price: float
    loss_charge_party: str = "supplier"

    @property
    def loss_g(self) -> float:
        return max(0.0, self.outgoing_weight_g - self.incoming_weight_g)

    @property
    def loss_rate(self) -> float:
        if self.outgoing_weight_g <= 0:
            return 0.0
        return (self.loss_g / self.outgoing_weight_g) * 100

    def total_amount(self) -> float:
        if self.loss_charge_party == "supplier":
            return self.processing_fee
        else:
            return self.processing_fee + self.loss_g * self.current_gold_price
