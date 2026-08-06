"""
Odoo model layer integration tests (24 tests + 6 placeholder outline)
tests: 01-12 金料, 13-15 工序报工, 16-18 印记, 19-21 旧金, 22-24 件级 SN
Plan: 25-30 金价/委外/集成 (supplementary)
Run: odoo-bin -d test_db -i gold_mes --test-enable --test-tags=gold_mes
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged("gold_mes", "post_install", "-at_install")
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

    def test_01_batch_create(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 5000.0,
        })
        self.assertEqual(b.available_weight_g, 5000.0)

    def test_02_batch_state_draft(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
        })
        self.assertEqual(b.state, "draft")

    def test_03_allocate(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
        })
        b.allocate(200.0)
        self.assertEqual(b.available_weight_g, 800.0)

    def test_04_allocate_overflow(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 100.0,
        })
        with self.assertRaises(UserError):
            b.allocate(200.0)

    def test_05_consume(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
        })
        b.allocate(500.0)
        b.consume(300.0)
        self.assertEqual(b.consumed_weight_g, 300.0)

    def test_06_consume_overflow(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 100.0,
        })
        b.allocate(50.0)
        with self.assertRaises(UserError):
            b.consume(100.0)


    def test_07_release(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
        })
        b.allocate(500.0)
        b.release(200.0)
        self.assertEqual(b.available_weight_g, 700.0)

    def test_08_balanced(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
        })
        b.allocate(300.0)
        b.consume(200.0)
        self.assertTrue(b.is_balanced())

    def test_09_imbalance(self):
        with self.assertRaises(ValidationError):
            self.env["gold.material.batch"].create({
                "product_id": self.product.id,
                "net_weight_g": 1000.0,
                "consumed_weight_g": 999.0,
            })

    def test_10_action_available(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
            "inspection_state": "passed",
        })
        b.action_available()
        self.assertEqual(b.state, "available")

    def test_11_action_lock(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
            "inspection_state": "passed",
        })
        b.action_available()
        b.action_lock()
        self.assertEqual(b.state, "locked")
        b.action_unlock()
        self.assertEqual(b.state, "available")

    def test_12_action_scrap(self):
        b = self.env["gold.material.batch"].create({
            "product_id": self.product.id,
            "net_weight_g": 1000.0,
            "inspection_state": "passed",
        })
        b.action_available()
        b.action_scrap()
        self.assertEqual(b.available_weight_g, 0.0)


@tagged('gold_mes', 'post_install', '-at_install')
class TestGoldWorkorderReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Ring Test', 'type': 'product',
        })
        cls.production = cls.env['mrp.production'].create({
            'product_id': cls.product.id,
            'product_qty': 10,
        })
        cls.operation = cls.env['gold.process.operation'].create({
            'code': 'T_OP01',
            'name': 'TestOp',
            'standard_loss_rate': 4.0,
        })

    def test_13_loss_calculation(self):
        b = self.env['gold.material.batch'].create({
            'product_id': self.product.id,
            'net_weight_g': 1000.0,
            'inspection_state': 'passed',
        })
        b.action_available()
        b.allocate(5.250)
        b.consume(5.250)
        r = self.env['gold.workorder.report'].create({
            'production_id': self.production.id,
            'operation_id': self.operation.id,
            'input_batch_id': b.id,
            'input_weight_g': 5.250,
            'output_weight_g': 5.180,
            'work_hours': 0.45,
            'operator_id': self.env.user.id,
        })
        self.assertAlmostEqual(r.loss_g, 0.070, places=6)
        self.assertAlmostEqual(r.loss_rate, 1.3333, places=4)

    def test_14_over_loss(self):
        b = self.env['gold.material.batch'].create({
            'product_id': self.product.id,
            'net_weight_g': 1000.0,
            'inspection_state': 'passed',
        })
        b.action_available()
        b.allocate(10.0)
        b.consume(10.0)
        r = self.env['gold.workorder.report'].create({
            'production_id': self.production.id,
            'operation_id': self.operation.id,
            'input_batch_id': b.id,
            'input_weight_g': 10.0,
            'output_weight_g': 5.0,
            'work_hours': 0.45,
            'operator_id': self.env.user.id,
        })
        self.assertTrue(r.is_over_loss)

    def test_15_quality_states(self):
        b = self.env['gold.material.batch'].create({
            'product_id': self.product.id,
            'net_weight_g': 1000.0,
            'inspection_state': 'passed',
        })
        b.action_available()
        b.allocate(10.0)
        b.consume(10.0)
        for q in ['passed', 'failed', 'rework']:
            r = self.env['gold.workorder.report'].create({
                'production_id': self.production.id,
                'operation_id': self.operation.id,
                'input_batch_id': b.id,
                'input_weight_g': 10.0,
                'output_weight_g': 9.8,
                'work_hours': 0.5,
                'operator_id': self.env.user.id,
                'quality_state': q,
            })
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('gold_mes', 'post_install', '-at_install')
class TestGoldImprint(TransactionCase):
    def test_16_three_role_separation(self):
        u = self.env['res.users'].create({'name': 'A', 'login': 'a_imprint', 'email': 'a@x.com'})
        p = self.env['product.product'].create({'name': 't', 'type': 'product'})
        with self.assertRaises(ValidationError):
            self.env['gold.imprint'].create({
                'operator_id': u.id, 'reviewer_id': u.id, 'encoder_id': u.id,
                'material_code': 'Au', 'purity_code': 'z',
                'factory_code': 'x', 'assay_code': 'y',
                'product_id': p.id, 'piece_sn': 't-001',
                'imprint_position': 'inside_ring',
            })

# === Step 4: Imprint + Recycle + Piece ===
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged("gold_mes", "post_install", "-at_install")
class TestGoldImprint(TransactionCase):

    def test_17_content_auto(self):
        p = self.env["product.product"].create({
            "name": "t",
            "type": "product",
        })
        op_u = self.env["res.users"].create({
            "name": "op",
            "login": "op_im",
            "email": "op@x.com",
        })
        rv_u = self.env["res.users"].create({
            "name": "rv",
            "login": "rv_im",
            "email": "rv@x.com",
        })
        en_u = self.env["res.users"].create({
            "name": "en",
            "login": "en_im",
            "email": "en@x.com",
        })
        im = self.env["gold.imprint"].create({
            "operator_id": op_u.id,
            "reviewer_id": rv_u.id,
            "encoder_id": en_u.id,
            "material_code": "Au",
            "purity_code": "z",
            "factory_code": "x",
            "assay_code": "y",
            "product_id": p.id,
            "piece_sn": "t-002",
            "imprint_position": "inside_ring",
        })
        self.assertEqual(im.imprint_content, "Au z x y")
    def test_18_ocr_verify_match(self):
        p = self.env["product.product"].create({
            "name": "t",
            "type": "product",
        })
        op_u = self.env["res.users"].create({
            "name": "op2",
            "login": "op_ocr2",
            "email": "op2@x.com",
        })
        rv_u = self.env["res.users"].create({
            "name": "rv2",
            "login": "rv_ocr2",
            "email": "rv2@x.com",
        })
        en_u = self.env["res.users"].create({
            "name": "en2",
            "login": "en_ocr2",
            "email": "en2@x.com",
        })
        im = self.env["gold.imprint"].create({
            "operator_id": op_u.id,
            "reviewer_id": rv_u.id,
            "encoder_id": en_u.id,
            "material_code": "Au",
            "purity_code": "18K",
            "factory_code": "X",
            "assay_code": "NGTC",
            "product_id": p.id,
            "piece_sn": "t-003",
            "imprint_position": "inside_ring",
        })
        self.assertTrue(im.action_ocr_verify("Au 18K X NGTC"))
        self.assertFalse(im.ocr_mismatch)

@tagged("gold_mes", "post_install", "-at_install")
class TestGoldRecycle(TransactionCase):
    def test_19_valuation(self):
        r = self.env["gold.recycle"].create({
            "partner_id": self.env["res.partner"].create({"name": "t", "is_company": False}).id,
            "id_number": "110101199001011234",
            "net_weight_g": 10.0,
            "xrf_purity": 99.5,
            "fire_purity": 99.5,
            "price_at_time": 580.0,
            "discount_factor": 0.97,
            "state": "draft",
        })
        self.assertAlmostEqual(r.valuation_amount, 5597.87, places=1)

    def test_20_large_amount(self):
        r = self.env["gold.recycle"].create({
            "partner_id": self.env["res.partner"].create({"name": "t", "is_company": False}).id,
            "id_number": "110101199001011235",
            "net_weight_g": 100.0,
            "xrf_purity": 99.5,
            "price_at_time": 580.0,
            "discount_factor": 0.97,
            "state": "draft",
        })
        self.assertTrue(r.is_large_amount)

    def test_21_invalid_purity(self):
        with self.assertRaises(ValidationError):
            self.env["gold.recycle"].create({
                "partner_id": self.env["res.partner"].create({"name": "t", "is_company": False}).id,
                "id_number": "110101199001011236",
                "net_weight_g": 10.0,
                "xrf_purity": 101.0,
                "price_at_time": 580.0,
            })


# === Step 4 finish: Piece SN (test_22-24) ===
@tagged("gold_mes", "post_install", "-at_install")
class TestGoldPiece(TransactionCase):
    def test_22_generate_sn(self):
        p = self.env["product.product"].create({
            "name": "t",
            "type": "product",
            "default_code": "R-TEST",
        })
        piece = self.env["gold.piece"].create({"product_id": p.id})
        self.assertTrue(piece.sn.startswith("GLD-"))

    def test_23_qr_payload(self):
        p = self.env["product.product"].create({"name": "t", "type": "product"})
        piece = self.env["gold.piece"].create({"product_id": p.id, "sn": "TEST-001"})
        self.assertEqual(piece.qr_payload, "https://verify.gold-mes.com/piece/TEST-001")

    def test_24_verify_by_sn(self):
        p = self.env["product.product"].create({"name": "t", "type": "product"})
        self.env["gold.piece"].create({"product_id": p.id, "sn": "VER-001"})
        result = self.env["gold.piece"].verify_by_sn("VER-001")
        self.assertTrue(result["found"])