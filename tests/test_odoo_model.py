"""
Odoo model layer integration tests.

Covers 24 happy-path / boundary tests:
  - 01-12 gold.material.batch      金料批次(创建/状态/分配/消耗/平衡/动作)
  - 13-15 gold.workorder.report    工序报工(损耗/超耗/质量)
  - 16-18 gold.imprint             印记(三级分离/内容/OCR)
  - 19-21 gold.recycle             旧金回收(估值/大额/无效含量)
  - 22-24 gold.piece               件级 SN(生成/二维码/扫码核验)

Run with Odoo test runner:
    odoo-bin -d test_db -i dunhuanggold_workshop_mes \\
        --test-enable --test-tags=dunhuanggold_workshop_mes \\
        --stop-after-init
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


# ============================================================
# 01-12  金料批次
# ============================================================

@tagged("dunhuanggold_workshop_mes", "post_install", "-at_install")
class TestGoldMaterialBatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({
            "name": "Au 9999 Test",
            "default_code": "AU9999-TEST",
            "gold_purity": 99.99,
            "type": "product",
        })

    def _make_batch(self, net=1000.0, inspection="pending", **extra):
        vals = {
            "product_id": self.product.id,
            "net_weight_g": net,
            "inspection_state": inspection,
        }
        vals.update(extra)
        return self.env["gold.material.batch"].create(vals)

    def test_01_batch_create(self):
        """新批次初始可用重量 = 净重"""
        b = self._make_batch(net=5000.0)
        self.assertEqual(b.available_weight_g, 5000.0)

    def test_02_batch_state_draft(self):
        """新批次默认草稿态"""
        b = self._make_batch(net=1000.0)
        self.assertEqual(b.state, "draft")

    def test_03_allocate(self):
        """分配后可用重量正确递减"""
        b = self._make_batch(net=1000.0)
        b.allocate(200.0)
        self.assertEqual(b.available_weight_g, 800.0)
        self.assertEqual(b.allocated_weight_g, 200.0)

    def test_04_allocate_overflow(self):
        """分配超过可用应报错"""
        b = self._make_batch(net=100.0)
        with self.assertRaises(UserError):
            b.allocate(200.0)

    def test_05_consume(self):
        """消耗后 consumed_weight_g 累加"""
        b = self._make_batch(net=1000.0)
        b.allocate(500.0)
        b.consume(300.0)
        self.assertEqual(b.consumed_weight_g, 300.0)
        self.assertEqual(b.allocated_weight_g, 200.0)

    def test_06_consume_overflow(self):
        """消耗超过已分配应报错"""
        b = self._make_batch(net=100.0)
        b.allocate(50.0)
        with self.assertRaises(UserError):
            b.consume(100.0)

    def test_07_release(self):
        """释放已分配恢复可用"""
        b = self._make_batch(net=1000.0)
        b.allocate(500.0)
        b.release(200.0)
        self.assertEqual(b.available_weight_g, 700.0)
        self.assertEqual(b.allocated_weight_g, 300.0)

    def test_08_balanced(self):
        """重量平衡校验通过"""
        b = self._make_batch(net=1000.0)
        b.allocate(300.0)
        b.consume(200.0)
        self.assertTrue(b.is_balanced())

    def test_09_imbalance(self):
        """强行制造不平衡应触发 ValidationError"""
        # 直接写 consumed_weight_g 但不同步 allocated/available,造成不平衡
        with self.assertRaises(ValidationError):
            self.env["gold.material.batch"].create({
                "product_id": self.product.id,
                "net_weight_g": 1000.0,
                "consumed_weight_g": 999.0,
            })

    def test_10_action_available(self):
        """检验通过 → action_available → available"""
        b = self._make_batch(net=1000.0, inspection="passed")
        b.action_available()
        self.assertEqual(b.state, "available")

    def test_11_action_lock_unlock(self):
        """available ↔ locked 双向切换"""
        b = self._make_batch(net=1000.0, inspection="passed")
        b.action_available()
        b.action_lock()
        self.assertEqual(b.state, "locked")
        b.action_unlock()
        self.assertEqual(b.state, "available")

    def test_12_action_scrap(self):
        """报废后可用重量归零"""
        b = self._make_batch(net=1000.0, inspection="passed")
        b.action_available()
        b.action_scrap()
        self.assertEqual(b.state, "scrap")
        self.assertEqual(b.available_weight_g, 0.0)


# ============================================================
# 13-15  工序报工
# ============================================================

@tagged("dunhuanggold_workshop_mes", "post_install", "-at_install")
class TestGoldWorkorderReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({
            "name": "Ring Test",
            "type": "product",
        })
        cls.production = cls.env["mrp.production"].create({
            "product_id": cls.product.id,
            "product_qty": 10,
        })
        cls.operation = cls.env["gold.process.operation"].create({
            "code": "T_OP01",
            "name": "TestOp",
            "standard_loss_rate": 4.0,
        })

    def _report(self, batch_net, input_g, output_g, confirm=True, **extra):
        """构造一个可用批次 + 报工记录(默认 confirm=True 走完整流程)"""
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": batch_net,
            "inspection_state": "passed",
        })
        b.action_available()
        # 报工确认时才扣减,所以先 allocate 即可
        b.allocate(input_g)
        rec = self.env["gold.workorder.report"].create({
            "production_id": self.production.id,
            "operation_id": self.operation.id,
            "input_batch_id": b.id,
            "input_weight_g": input_g,
            "output_weight_g": output_g,
            "work_hours": 0.45,
            "operator_id": self.env.user.id,
            **extra,
        })
        if confirm:
            rec.action_confirm()
        return rec

    def test_13_loss_calculation(self):
        """损耗量与损耗率计算正确(0.070g / 1.3333%)"""
        r = self._report(batch_net=1000.0, input_g=5.250, output_g=5.180)
        self.assertAlmostEqual(r.loss_g, 0.070, places=6)
        self.assertAlmostEqual(r.loss_rate, 1.3333, places=4)

    def test_14_over_loss(self):
        """损耗 50% 远超定额 4% 应触发超耗预警"""
        r = self._report(batch_net=1000.0, input_g=10.0, output_g=5.0)
        self.assertTrue(r.is_over_loss)

    def test_15_quality_states(self):
        """三种质量判定(passed / failed / rework)都应能正常写入并确认"""
        # 一个批次 30g,3 次报工各 10g
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
            "inspection_state": "passed",
        })
        b.action_available()
        b.allocate(30.0)
        for q in ["passed", "failed", "rework"]:
            r = self.env["gold.workorder.report"].create({
                "production_id": self.production.id,
                "operation_id": self.operation.id,
                "input_batch_id": b.id,
                "input_weight_g": 10.0,
                "output_weight_g": 9.8,
                "work_hours": 0.5,
                "operator_id": self.env.user.id,
                "quality_state": q,
            })
            r.action_confirm()
            self.assertEqual(r.quality_state, q)
            self.assertEqual(r.state, "confirmed")


# ============================================================
# 16-18  印记
# ============================================================

@tagged("dunhuanggold_workshop_mes", "post_install", "-at_install")
class TestGoldImprint(TransactionCase):
    def _users(self):
        return [
            self.env["res.users"].create({"name": "op", "login": "op_im_test", "email": "op@x.com"}),
            self.env["res.users"].create({"name": "rv", "login": "rv_im_test", "email": "rv@x.com"}),
            self.env["res.users"].create({"name": "en", "login": "en_im_test", "email": "en@x.com"}),
        ]

    def _product(self):
        return self.env["product.product"].create({"name": "imprint-test", "type": "product"})

    def test_16_three_role_separation(self):
        """操作员/复核员/编码员三者必须分离(GB 11887-2012 §4.1)"""
        u = self.env["res.users"].create({"name": "A", "login": "a_imprint_3r", "email": "a@x.com"})
        p = self._product()
        with self.assertRaises(ValidationError):
            self.env["gold.imprint"].create({
                "operator_id": u.id,
                "reviewer_id": u.id,
                "encoder_id": u.id,
                "material_code": "Au",
                "purity_code": "z",
                "factory_code": "x",
                "assay_code": "y",
                "product_id": p.id,
                "piece_sn": "t-001",
                "imprint_position": "inside_ring",
            })

    def test_17_content_auto(self):
        """印记内容 = 材质 + 纯度 + 厂印 + 检测中心,空格拼接"""
        op, rv, en = self._users()
        im = self.env["gold.imprint"].create({
            "operator_id": op.id,
            "reviewer_id": rv.id,
            "encoder_id": en.id,
            "material_code": "Au",
            "purity_code": "z",
            "factory_code": "x",
            "assay_code": "y",
            "product_id": self._product().id,
            "piece_sn": "t-002",
            "imprint_position": "inside_ring",
        })
        self.assertEqual(im.imprint_content, "Au z x y")

    def test_18_ocr_verify_match(self):
        """OCR 内容匹配应返回 True,无 mismatch"""
        op, rv, en = self._users()
        im = self.env["gold.imprint"].create({
            "operator_id": op.id,
            "reviewer_id": rv.id,
            "encoder_id": en.id,
            "material_code": "Au",
            "purity_code": "18K",
            "factory_code": "X",
            "assay_code": "NGTC",
            "product_id": self._product().id,
            "piece_sn": "t-003",
            "imprint_position": "inside_ring",
        })
        self.assertTrue(im.action_ocr_verify("Au 18K X NGTC"))
        self.assertFalse(im.ocr_mismatch)


# ============================================================
# 19-21  旧金回收
# ============================================================

@tagged("dunhuanggold_workshop_mes", "post_install", "-at_install")
class TestGoldRecycle(TransactionCase):
    def _partner(self, id_no):
        return self.env["res.partner"].create({
            "name": f"cust-{id_no[-4:]}",
            "is_company": False,
        })

    def _vals(self, id_no, **extra):
        vals = {
            "partner_id": self._partner(id_no).id,
            "id_number": id_no,
            "net_weight_g": 10.0,
            "xrf_purity": 99.5,
            "fire_purity": 99.5,
            "price_at_time": 580.0,
            "discount_factor": 0.97,
            "state": "draft",
        }
        vals.update(extra)
        return vals

    def test_19_valuation(self):
        """旧金回收估价: 10g × 99.5% × 580 × 0.97 ≈ 5597.87"""
        r = self.env["gold.recycle"].create(self._vals("110101199001011234"))
        self.assertAlmostEqual(r.valuation_amount, 5597.87, places=1)

    def test_20_large_amount(self):
        """100g × 99.5% × 580 × 0.97 ≈ 5.6万,触发 AML 大额标志"""
        r = self.env["gold.recycle"].create(self._vals("110101199001011235", net_weight_g=100.0))
        self.assertTrue(r.is_large_amount)

    def test_21_invalid_purity(self):
        """含量超 100 应触发 ValidationError"""
        with self.assertRaises(ValidationError):
            self.env["gold.recycle"].create(self._vals(
                "110101199001011236",
                xrf_purity=101.0,
            ))


# ============================================================
# 22-24  件级 SN
# ============================================================

@tagged("dunhuanggold_workshop_mes", "post_install", "-at_install")
class TestGoldPiece(TransactionCase):
    def test_22_generate_sn(self):
        """新件级 SN 自动生成 GLD- 前缀"""
        p = self.env["product.product"].create({
            "name": "t",
            "type": "product",
            "default_code": "R-TEST",
        })
        piece = self.env["gold.piece"].create({"product_id": p.id})
        self.assertTrue(piece.sn.startswith("GLD-"))

    def test_23_qr_payload(self):
        """件级 SN 扫码 payload = verify URL"""
        p = self.env["product.product"].create({"name": "t", "type": "product"})
        piece = self.env["gold.piece"].create({"product_id": p.id, "sn": "TEST-001"})
        self.assertEqual(
            piece.qr_payload,
            "https://verify.dunhuang-gold-mes.com/piece/TEST-001",
        )

    def test_24_verify_by_sn(self):
        """扫码核验:存在 SN 应能查到"""
        p = self.env["product.product"].create({"name": "t", "type": "product"})
        self.env["gold.piece"].create({"product_id": p.id, "sn": "VER-001"})
        result = self.env["gold.piece"].verify_by_sn("VER-001")
        self.assertTrue(result.get("found"))
