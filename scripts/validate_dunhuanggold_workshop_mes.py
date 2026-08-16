#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Odoo 模块基础验证 (无 Odoo 依赖)"""
import os
import re
import sys
import ast
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "addons" / "dunhuanggold_workshop_mes"
MANIFEST = BASE_DIR / "__manifest__.py"


def log(name, ok):
    sign = "✓" if ok else "✗"
    print(f"  {sign} {name}")
    return ok


def info(msg):
    print(f"[INFO] {msg}")


def check_python():
    info("Python 语法")
    success = True
    for root, _, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith(".py"):
                path = Path(root) / f
                try:
                    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                    success &= log(str(path.relative_to(BASE_DIR)), True)
                except Exception as e:
                    success &= log(f"{path}: {e}", False)
    return success


def check_xml():
    info("XML 格式")
    success = True
    for root, _, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith(".xml"):
                path = Path(root) / f
                try:
                    ET.parse(path)
                    success &= log(str(path.relative_to(BASE_DIR)), True)
                except Exception as e:
                    success &= log(f"{path}: {e}", False)
    return success


def check_manifest():
    info("manifest data 文件")
    if not MANIFEST.exists():
        return log("manifest", False)
    text = MANIFEST.read_text(encoding="utf-8")
    section = re.search(r'"data"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if not section:
        return log("data section", False)
    success = True
    for m in re.finditer(r'"([^"]+)"', section.group(1)):
        rel = m.group(1)
        path = BASE_DIR / rel
        success &= log(rel, path.exists())
    return success


def extract_models():
    """提取 _name 模型"""
    info("提取 _name 模型")
    models = {}
    models_dir = BASE_DIR / "models"
    for root, _, files in os.walk(models_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = Path(root) / f
            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for stmt in node.body:
                        if isinstance(stmt, ast.Assign):
                            if len(stmt.targets) != 1:
                                continue
                            target = stmt.targets[0]
                            if not isinstance(target, ast.Name):
                                continue
                            if target.id != "_name":
                                continue
                            if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                                models[stmt.value.value] = str(path.relative_to(BASE_DIR))
    return models


def check_csv():
    info("access CSV 引用")
    csv_path = BASE_DIR / "security" / "ir.model.access.csv"
    if not csv_path.exists():
        return log("csv", False)
    models = extract_models()
    success = True
    csv_lines = [
        line for line in csv_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("id,")
    ]
    for line in csv_lines:
        parts = line.split(",")
        if len(parts) < 3:
            continue
        model_id = parts[2].strip()
        if model_id.startswith("model_"):
            # Odoo 标准: model_<model_name_with_underscores>
            # 我们的 _name 是 'gold.xxx.yyy' 命名空间,故 model_id 应为 model_gold_xxx_yyy
            # 验证脚本: 反向把 _ 替换为 . 还原为 _name
            model_name_uns = model_id.replace("model_", "", 1)
            # 尝试: 已存在 _name
            if model_name_uns in models:
                success &= log(model_name_uns, True)
                continue
            # 尝试: _ 替换为 . 后是 _name
            model_name_dot = model_name_uns.replace("_", ".")
            if model_name_dot in models:
                success &= log(f"{model_name_uns} ({model_name_dot})", True)
                continue
            success &= log(f"{model_name_uns} -> {model_name_dot}", False)
    print(f"  total: {len(csv_lines)} refs, {len(models)} models in models/")
    return success


def check_actions():
    info("menu action 引用")
    menu = BASE_DIR / "views" / "menus.xml"
    text = menu.read_text(encoding="utf-8")
    actions = set(re.findall(r'action="([^"]+)"', text))
    success = True
    for action in actions:
        found = False
        for root, _, files in os.walk(BASE_DIR):
            for f in files:
                if not f.endswith(".xml"):
                    continue
                p = Path(root) / f
                try:
                    t = p.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if re.search(rf'<record\s+id="{re.escape(action)}"', t):
                    found = True
                    break
            if found:
                break
        is_external = action.startswith("product.") or action.startswith("stock.")
        success &= log(f"{action}{' (外部)' if not found and is_external else ''}",
                       found or is_external)
    return success


def main():
    print("=" * 60)
    print("敦煌金加工车间 ERP — 模块验证")
    print("=" * 60)
    results = [
        ("Python 语法", check_python()),
        ("XML 格式", check_xml()),
        ("manifest data", check_manifest()),
        ("access CSV", check_csv()),
        ("menu action", check_actions()),
    ]
    print()
    print("=" * 60)
    print("汇总")
    print("=" * 60)
    failed = 0
    for name, ok in results:
        sign = "✓" if ok else "✗"
        print(f"  {sign} {name}")
        if not ok:
            failed += 1
    print()
    if failed == 0:
        print("✅ 全部检查通过")
        return 0
    print(f"❌ {failed} 项检查失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
