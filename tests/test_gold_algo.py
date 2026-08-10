"""
敦煌金加工车间 ERP — 核心算法单元测试
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from gold_core import (
    GRAM, MILLIGRAM, TROY_OUNCE, QIAN, LIANG, CARAT,
    ProcessOperation,
    OIL_PRESS_OPS, LOST_WAX_OPS,
    calculate_total_loss_rate, calculate_total_time,
    calculate_gold_cost,
    calculate_recycle_valuation, is_large_amount,
    lock_price,
    Mold,
    MaterialBatch,
    WorkorderReport,
    PieceSN,
    OutsourceOrder,
)


class TestMeasurement(unittest.TestCase):
    def test_gram(self):
        self.assertEqual(GRAM.to_gram(5.0), 5.0)
        self.assertEqual(GRAM.from_gram(5.0), 5.0)

    def test_milligram(self):
        self.assertEqual(MILLIGRAM.to_gram(1000), 1.0)

    def test_oz(self):
        self.assertAlmostEqual(TROY_OUNCE.to_gram(1.0), 31.1034768, places=6)

    def test_qian(self):
        self.assertAlmostEqual(QIAN.to_gram(1.0), 3.75, places=6)

    def test_liang(self):
        self.assertAlmostEqual(LIANG.to_gram(1.0), 37.5, places=6)

    def test_carat(self):
        self.assertAlmostEqual(CARAT.to_gram(5.0), 1.0, places=6)


class TestLossRate(unittest.TestCase):
    def test_oil_press(self):
        rate = calculate_total_loss_rate(OIL_PRESS_OPS)
        self.assertAlmostEqual(rate, 8.7142, places=3)

    def test_lost_wax(self):
        rate = calculate_total_loss_rate(LOST_WAX_OPS)
        self.assertAlmostEqual(rate, 18.2859, places=3)

    def test_zero(self):
        op = ProcessOperation("X", "无损耗", 1.0, 0.0)
        self.assertEqual(calculate_total_loss_rate([op]), 0.0)

    def test_total_time(self):
        self.assertAlmostEqual(calculate_total_time(OIL_PRESS_OPS), 8.67, places=2)


class TestGoldCost(unittest.TestCase):
    def test_basic(self):
        cost = calculate_gold_cost(5.2, 8.7142, 580.0)
        self.assertAlmostEqual(cost["gold_cost"], 3278.82, places=1)

    def test_full(self):
        cost = calculate_gold_cost(
            finished_weight_g=5.2, total_loss_rate=8.7142, current_price=580.0,
            processing_fee=80.0, stone_cost=2400.0, plating_cost=150.0,
            packaging_cost=15.0, detection_cost=30.0, design_cost=50.0,
            profit_margin=20.0,
        )
        self.assertAlmostEqual(cost["gold_cost"], 3278.82, places=1)
        self.assertAlmostEqual(cost["total_cost"], 6003.82, places=1)
        self.assertAlmostEqual(cost["with_profit"], 7204.58, places=1)


class TestRecycle(unittest.TestCase):
    def test_valuation(self):
        v = calculate_recycle_valuation(10.0, 99.5, 580.0, 0.97)
        self.assertAlmostEqual(v["pure_g"], 9.95, places=4)
        self.assertAlmostEqual(v["valuation"], 5597.87, places=1)

    def test_invalid_purity(self):
        with self.assertRaises(ValueError):
            calculate_recycle_valuation(10.0, -1.0, 580.0)
        with self.assertRaises(ValueError):
            calculate_recycle_valuation(10.0, 101.0, 580.0)

    def test_invalid_discount(self):
        with self.assertRaises(ValueError):
            calculate_recycle_valuation(10.0, 99.5, 580.0, 1.5)

    def test_large_amount(self):
        self.assertFalse(is_large_amount(1000.0))
        self.assertTrue(is_large_amount(50000.0))


class TestPriceLock(unittest.TestCase):
    def test_init(self):
        lock = lock_price(580.0, lock_minutes=30)
        self.assertEqual(lock.price, 580.0)
        self.assertEqual(lock.gold_type, "au9999")

    def test_remaining(self):
        lock = lock_price(580.0, lock_minutes=30)
        self.assertAlmostEqual(lock.remaining_minutes(), 30.0, places=1)

    def test_expired(self):
        lock = lock_price(580.0, lock_minutes=-1)
        self.assertTrue(lock.is_expired())


class TestMold(unittest.TestCase):
    def test_remaining(self):
        m = Mold(code="M", name="t", rated_life_count=1000, used_count=200)
        self.assertEqual(m.remaining_count, 800)

    def test_critical(self):
        m = Mold(code="M", name="t", rated_life_count=1000, used_count=950)
        self.assertTrue(m.is_critical())

    def test_scrapped(self):
        m = Mold(code="M", name="t", rated_life_count=1000, used_count=1000)
        self.assertTrue(m.is_scrapped())


class TestMaterialBatch(unittest.TestCase):
    def test_initial(self):
        b = MaterialBatch(batch_no="x", net_weight_g=5000.0)
        self.assertEqual(b.available_weight_g, 5000.0)

    def test_allocate(self):
        b = MaterialBatch(batch_no="x", net_weight_g=100.0)
        b.allocate(20.0)
        self.assertEqual(b.available_weight_g, 80.0)

    def test_allocate_exceed(self):
        b = MaterialBatch(batch_no="x", net_weight_g=10.0)
        with self.assertRaises(ValueError):
            b.allocate(20.0)

    def test_consume(self):
        b = MaterialBatch(batch_no="x", net_weight_g=100.0)
        b.allocate(50.0)
        b.consume(30.0)
        self.assertEqual(b.available_weight_g, 50.0)
        self.assertEqual(b.consumed_weight_g, 30.0)

    def test_balance(self):
        b = MaterialBatch(batch_no="x", net_weight_g=1000.0)
        b.allocate(100.0)
        b.consume(50.0)
        self.assertTrue(b.is_balanced())


class TestWorkorderReport(unittest.TestCase):
    def test_loss(self):
        r = WorkorderReport("OP", 5.250, 5.180, 4.0)
        self.assertAlmostEqual(r.loss_g, 0.070, places=3)
        self.assertAlmostEqual(r.loss_rate, 1.3333, places=4)

    def test_over_loss(self):
        r = WorkorderReport("LWC06", 10.0, 5.0, 10.0)
        self.assertTrue(r.is_over_loss())


class TestPieceSN(unittest.TestCase):
    def test_generate(self):
        sn = PieceSN.generate("RING-001", 42, 1, datetime(2026, 8, 5))
        self.assertEqual(sn, "GLD-20260805-RING-001-00001")

    def test_qr(self):
        sn = "GLD-20260805-RING-001-00001"
        p = PieceSN(sn=sn, product_code="RING-001", production_id=42)
        self.assertEqual(p.qr_payload, f"https://verify.dunhuang-gold-mes.com/piece/{sn}")


class TestOutsource(unittest.TestCase):
    def test_supplier_loss(self):
        o = OutsourceOrder("X", 10.0, 9.85, 200.0, 580.0, "supplier")
        self.assertEqual(o.total_amount(), 200.0)

    def test_self_loss(self):
        o = OutsourceOrder("X", 10.0, 9.85, 200.0, 580.0, "self")
        self.assertAlmostEqual(o.total_amount(), 287.0, places=1)


class TestIntegration(unittest.TestCase):
    def test_full_order(self):
        """完整订单流程"""
        ops = OIL_PRESS_OPS
        total_loss = calculate_total_loss_rate(ops)

        mold = Mold(code="M", name="t", rated_life_count=1000000, used_count=100)
        self.assertFalse(mold.is_critical())

        batch = MaterialBatch(batch_no="x", net_weight_g=5000.0)
        required = 5.2 * (1 + total_loss / 100.0)
        batch.allocate(required)
        batch.consume(required)
        self.assertTrue(batch.is_balanced())

        # 单工序损耗(执模 = 4%) vs 工艺路线总损耗不可比
        # 这里重新设计:投入 5.65g,工序(执模)损耗 4%,产出 5.42g
        single_op_weight = 5.2
        op_loss = 4.0
        op_input = single_op_weight / (1 - op_loss / 100.0)
        r = WorkorderReport("OWP06", op_input, single_op_weight, op_loss)
        self.assertAlmostEqual(r.loss_rate, op_loss, places=2)

        cost = calculate_gold_cost(5.2, total_loss, 580.0, processing_fee=80, profit_margin=20.0)
        self.assertGreater(cost["with_profit"], 0)

        sn = PieceSN.generate("RING-001", 42, 1, datetime(2026, 8, 5))
        self.assertTrue(sn.startswith("GLD-"))

    def test_lost_wax(self):
        ops = LOST_WAX_OPS
        total_loss = calculate_total_loss_rate(ops)
        self.assertAlmostEqual(total_loss, 18.2859, places=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
