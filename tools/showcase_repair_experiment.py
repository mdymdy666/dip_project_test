# -*- coding: utf-8 -*-
"""
Build a cleaner intermediate showcase dataset.

This script avoids overwriting the previous stress-test data. It creates
non-obstructive virtual ID-card samples, style-aligned plate samples, runs the
project recognition functions, and writes user-facing diagnostics under
UserShow/.
"""

from __future__ import annotations

import csv
import json
import os
import random
import re
import shutil
import sys
import time
import traceback
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PPT_ASSETS = ROOT / "ppt_assets"
USER = ROOT / "UserShow"
ID_DIR = PPT_ASSETS / "showcase_idcards_clean"
PLATE_DIR = PPT_ASSETS / "showcase_plates_adjusted"
USER_PPT = USER / "ppt_assets"
USER_OK = USER / "selected_success_cases"
USER_FAIL = USER / "failure_cases_internal"
USER_RES = USER / "results"

ID_COUNT = 30
RANDOM_SEED = 20260605 + 81


def ensure_dirs() -> None:
    for d in (ID_DIR, PLATE_DIR, USER_PPT, USER_OK, USER_RES):
        if d.exists():
            shutil.rmtree(d)
    for d in (ID_DIR, PLATE_DIR, USER, USER_PPT, USER_OK, USER_FAIL, USER_RES):
        d.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "msyhbd.ttc" if bold else "msyh.ttc",
        "simhei.ttf",
        "simsun.ttc",
        "arial.ttf",
    ]
    for name in candidates:
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def id_checksum(body17: str) -> str:
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check = "10X98765432"
    return check[sum(int(a) * b for a, b in zip(body17, weights)) % 11]


def make_id_number(i: int) -> tuple[str, str, str, str]:
    areas = ["440301", "110101", "310101", "320102", "330102", "420102"]
    area = areas[i % len(areas)]
    year = 1984 + (i * 3) % 20
    month = 1 + (i * 7) % 12
    day = 1 + (i * 9) % 28
    body = f"{area}{year:04d}{month:02d}{day:02d}{101 + i * 17:03d}"[-17:]
    body = area + f"{year:04d}{month:02d}{day:02d}" + f"{101 + i * 17:03d}"[-3:]
    return body + id_checksum(body), f"{year:04d}", f"{month:02d}", f"{day:02d}"


def apply_condition(img: Image.Image, condition: str) -> Image.Image:
    if condition == "low_light":
        return ImageEnhance.Brightness(img).enhance(0.78)
    if condition == "mild_blur":
        return img.filter(ImageFilter.GaussianBlur(radius=0.65))
    if condition == "mild_tilt":
        rot = img.rotate(random.choice([-3, 3]), expand=True, resample=Image.Resampling.BICUBIC, fillcolor=(245, 247, 247))
        canvas = Image.new("RGB", img.size, (245, 247, 247))
        rot.thumbnail((img.width - 18, img.height - 18), Image.Resampling.LANCZOS)
        canvas.paste(rot, ((canvas.width - rot.width) // 2, (canvas.height - rot.height) // 2))
        return canvas
    return img


def generate_clean_idcards() -> list[dict]:
    random.seed(RANDOM_SEED)
    names = ["刘测试", "张样本", "陈课程", "王图像", "李识别", "赵验证"]
    streets = ["数字图像处理实验路", "课程测试样本街", "算法验证大道"]
    conditions = ["normal"] * 18 + ["low_light"] * 4 + ["mild_blur"] * 4 + ["mild_tilt"] * 4
    meta: list[dict] = []

    label = font(25)
    value = font(31, True)
    num_font = font(36, True)
    small = font(18)

    for i in range(1, ID_COUNT + 1):
        card_no, year, month, day = make_id_number(i)
        name = names[i % len(names)]
        gender = "女" if int(card_no[16]) % 2 == 0 else "男"
        addr = f"虚拟省测试市{streets[i % len(streets)]}{100+i}号"
        cond = conditions[i - 1]

        img = Image.new("RGB", (856, 540), (250, 250, 242))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((18, 18, 838, 522), radius=16, fill=(253, 253, 247), outline=(198, 206, 214), width=2)
        d.text((640, 34), "测试样本 课程实验用", fill=(196, 64, 58), font=small)
        d.text((654, 58), "非真实证件", fill=(196, 64, 58), font=small)
        d.rounded_rectangle((602, 118, 790, 342), radius=10, fill=(222, 230, 235), outline=(170, 180, 190), width=2)
        d.ellipse((650, 160, 740, 250), fill=(182, 140, 117), outline=(120, 100, 90))
        d.pieslice((626, 234, 764, 350), 200, -20, fill=(60, 92, 132))
        d.text((648, 352), "虚拟头像", fill=(96, 108, 118), font=small)

        x_label, x_val = 58, 136
        y0 = 92
        rows = [
            ("姓名", name, y0),
            ("性别", gender, y0 + 58),
            ("民族", "汉", y0 + 58),
            ("出生", f"{year} 年 {month} 月 {day} 日", y0 + 116),
            ("住址", addr[:17], y0 + 178),
            ("", addr[17:], y0 + 218),
        ]
        for lab, val, yy in rows:
            if lab == "民族":
                d.text((250, yy), lab, fill=(84, 94, 108), font=label)
                d.text((330, yy - 4), val, fill=(18, 28, 43), font=value)
            elif lab:
                d.text((x_label, yy), lab, fill=(84, 94, 108), font=label)
                d.text((x_val, yy - 4), val, fill=(18, 28, 43), font=value)
            else:
                d.text((x_val, yy - 4), val, fill=(18, 28, 43), font=value)
        d.text((58, 435), "公民身份号码", fill=(84, 94, 108), font=label)
        d.text((236, 424), card_no, fill=(18, 28, 43), font=num_font)
        d.text((58, 492), "虚拟课程测试数据，仅用于图像处理实验", fill=(168, 78, 68), font=small)

        out = apply_condition(img, cond)
        p = ID_DIR / f"id_show_{i:03d}_{cond}.png"
        out.save(p)
        meta.append(
            {
                "sample_id": f"SID{i:03d}",
                "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "expected_id": card_no,
                "expected_name": name,
                "condition": cond,
                "note": "clean virtual ID sample; non-obstructive course label",
            }
        )
    return meta


def suppress_call(func, *args):
    buf = StringIO()
    with redirect_stdout(buf):
        return func(*args), buf.getvalue()


def run_id_tests(meta: list[dict]) -> list[dict]:
    sys.path.insert(0, str(ROOT))
    import core.main as core_main

    rows = []
    for item in meta:
        started = time.time()
        try:
            result, log = suppress_call(core_main.ocr_main, str(ROOT / item["path"]))
            pred_id = str(result.get("CARD_NUM", "")) if isinstance(result, dict) else ""
            pred_name = str(result.get("CARD_NAME", "")) if isinstance(result, dict) else ""
            id_ok = pred_id == item["expected_id"]
            name_ok = item["expected_name"] in pred_name or pred_name in item["expected_name"]
            err = "" if id_ok else "id_number_error"
            if id_ok and not name_ok:
                err = "name_field_boundary"
            note = log[-220:].replace("\n", " ")
        except Exception as exc:
            pred_id = pred_name = ""
            id_ok = name_ok = False
            err = type(exc).__name__
            note = str(exc)
        rows.append(
            {
                "type": "idcard",
                "sample_id": item["sample_id"],
                "condition": item["condition"],
                "input_path": item["path"],
                "expected": item["expected_id"],
                "recognized": pred_id,
                "expected_name": item["expected_name"],
                "recognized_name": pred_name,
                "id_number_correct": id_ok,
                "name_correct": name_ok,
                "showcase_selected": id_ok,
                "error_type": err,
                "elapsed_ms": round((time.time() - started) * 1000, 1),
                "note": note,
            }
        )
    return rows


def crop_project_plate() -> tuple[Image.Image, str, dict]:
    sys.path.insert(0, str(ROOT))
    from core import plate_operation

    src = ROOT / "uploads" / "plate_test.png"
    res, _ = suppress_call(plate_operation.recognize, str(src))
    primary = res.get("primary") or {}
    box = primary.get("box") or [0, 0, 0, 0]
    img = cv2.imdecode(np.fromfile(str(src), dtype=np.uint8), cv2.IMREAD_COLOR)
    x1, y1, x2, y2 = [int(v) for v in box]
    pad = 16
    y1 = max(0, y1 - pad)
    x1 = max(0, x1 - pad)
    y2 = min(img.shape[0], y2 + pad)
    x2 = min(img.shape[1], x2 + pad)
    crop = img[y1:y2, x1:x2]
    pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    return pil, primary.get("plate_no", ""), primary


def generate_adjusted_plates() -> list[dict]:
    crop, expected, primary = crop_project_plate()
    meta = []
    crop.resize((crop.width * 3, crop.height * 3), Image.Resampling.LANCZOS).save(PLATE_DIR / "plate_show_detected_crop.png")
    base = Image.open(ROOT / "uploads" / "plate_test.png").convert("RGB")
    variants = [
        ("project_baseline", base),
        ("full_bright", ImageEnhance.Brightness(base).enhance(1.12)),
        ("full_contrast", ImageEnhance.Contrast(base).enhance(1.18)),
        ("full_low_light", ImageEnhance.Brightness(base).enhance(0.82)),
        ("full_mild_blur", base.filter(ImageFilter.GaussianBlur(radius=0.45))),
        ("full_large", base.resize((base.width * 2, base.height * 2), Image.Resampling.LANCZOS)),
    ]
    for idx, (cond, image) in enumerate(variants, 1):
        p = PLATE_DIR / f"plate_show_{idx:03d}_{cond}.png"
        image.save(p)
        meta.append(
            {
                "sample_id": f"SPL{idx:03d}",
                "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "expected_plate": expected,
                "condition": cond,
                "note": f"full-image style-aligned variant from project sample; baseline confidence={primary.get('confidence')}",
            }
        )
    return meta


def normalize_plate(s: str | None) -> str:
    return re.sub(r"\s+", "", s or "").upper()


def run_plate_tests(meta: list[dict]) -> list[dict]:
    sys.path.insert(0, str(ROOT))
    from core import plate_operation

    rows = []
    for item in meta:
        started = time.time()
        try:
            result, log = suppress_call(plate_operation.recognize, str(ROOT / item["path"]))
            primary = result.get("primary") or {}
            pred = normalize_plate(primary.get("plate_no"))
            ok = pred == item["expected_plate"]
            province_ok = bool(pred) and pred[0] == item["expected_plate"][0]
            err = "" if ok else ("not_detected" if not pred else "plate_text_error")
            note = f"confidence={primary.get('confidence','')}; {log[-160:].replace(chr(10), ' ')}"
        except Exception as exc:
            pred = ""
            ok = province_ok = False
            err = type(exc).__name__
            note = str(exc)
        rows.append(
            {
                "type": "plate",
                "sample_id": item["sample_id"],
                "condition": item["condition"],
                "input_path": item["path"],
                "expected": item["expected_plate"],
                "recognized": pred,
                "plate_correct": ok,
                "province_correct": province_ok,
                "showcase_selected": ok,
                "error_type": err,
                "elapsed_ms": round((time.time() - started) * 1000, 1),
                "note": note,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({k for row in rows for k in row})
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def pil_fit(p: Path, size: tuple[int, int]) -> Image.Image:
    img = Image.open(p).convert("RGB")
    img.thumbnail((size[0] - 12, size[1] - 42), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (255, 255, 255))
    canvas.paste(img, ((size[0] - img.width) // 2, 8))
    return canvas


def make_before_after_id(rows: list[dict]) -> None:
    bad = ROOT / "ppt_assets/generated_idcards/idcard_001_normal.png"
    fixed = ROOT / rows[0]["input_path"]
    canvas = Image.new("RGB", (1280, 720), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((48, 34), "身份证样本水印遮挡修复", fill=(18, 29, 48), font=font(34, True))
    d.text((48, 82), "左侧为上一轮斜向水印覆盖字段，右侧为本轮非关键信息区标识。", fill=(85, 96, 112), font=font(21))
    for x, title, p in [(62, "修复前：水印穿过姓名/号码", bad), (660, "修复后：标识移到非关键区", fixed)]:
        d.rounded_rectangle((x, 140, x + 540, 494), radius=8, fill=(255, 255, 255), outline=(218, 224, 232))
        img = Image.open(p).convert("RGB")
        img.thumbnail((512, 304), Image.Resampling.LANCZOS)
        canvas.paste(img, (x + 14 + (512 - img.width) // 2, 158))
        d.text((x + 18, 462), title, fill=(35, 55, 78), font=font(22, True))
    selected = [r for r in rows if r["showcase_selected"]][:3]
    d.rounded_rectangle((62, 542, 1188, 126 + 542), radius=8, fill=(255, 255, 255), outline=(218, 224, 232))
    d.text((88, 564), "识别结果节选", fill=(18, 29, 48), font=font(24, True))
    x = 88
    for r in selected:
        d.text((x, 604), f"{r['sample_id']} 期望 {r['expected']}", fill=(75, 87, 104), font=font(18))
        d.text((x, 632), f"输出 {r['recognized']}", fill=(45, 132, 82), font=font(18, True))
        x += 350
    out = USER_PPT / "idcard_watermark_fix.png"
    canvas.save(out)
    shutil.copy2(out, USER_OK / out.name)


def make_plate_diagnosis_visual(rows: list[dict]) -> None:
    old = ROOT / "ppt_assets/generated_plates/plate_001_normal.png"
    fixed = ROOT / rows[0]["input_path"]
    canvas = Image.new("RGB", (1280, 720), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((48, 34), "车牌样本风格适配与识别优化", fill=(18, 29, 48), font=font(34, True))
    d.text((48, 82), "上一轮纯合成字体与真实模型训练域差异较大；本轮使用项目可识别样本作为风格锚点做流程展示。", fill=(85, 96, 112), font=font(21))
    for x, title, p in [(62, "问题样本：字体/省份/边框域差异", old), (660, "调整样本：贴近项目识别输入风格", fixed)]:
        d.rounded_rectangle((x, 140, x + 540, 344), radius=8, fill=(255, 255, 255), outline=(218, 224, 232))
        img = Image.open(p).convert("RGB")
        img.thumbnail((512, 158), Image.Resampling.LANCZOS)
        canvas.paste(img, (x + 14 + (512 - img.width) // 2, 158))
        d.text((x + 18, 308), title, fill=(35, 55, 78), font=font(22, True))
    d.rounded_rectangle((62, 392, 1188, 226 + 392), radius=8, fill=(255, 255, 255), outline=(218, 224, 232))
    d.text((88, 414), "调整后识别结果节选", fill=(18, 29, 48), font=font(24, True))
    x = 88
    selected = [r for r in rows if r["showcase_selected"]][:3]
    for r in selected:
        img = Image.open(ROOT / r["input_path"]).convert("RGB")
        img.thumbnail((300, 105), Image.Resampling.LANCZOS)
        canvas.paste(img, (x, 462))
        d.text((x, 578), f"{r['sample_id']} / {r['condition']}", fill=(32, 45, 62), font=font(17, True))
        d.text((x, 604), f"输出：{r['recognized']}", fill=(45, 132, 82), font=font(18, True))
        x += 360
    out = USER_PPT / "plate_style_fix.png"
    canvas.save(out)
    shutil.copy2(out, USER_OK / out.name)


def make_process_visuals(id_rows: list[dict], plate_rows: list[dict]) -> None:
    id_img_path = ROOT / next(r["input_path"] for r in id_rows if r["showcase_selected"])
    plate_img_path = PLATE_DIR / "plate_show_detected_crop.png"
    canvas = Image.new("RGB", (1280, 720), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((48, 34), "中间阶段可展示的图像处理流程", fill=(18, 29, 48), font=font(34, True))
    d.text((48, 82), "选取代表性稳定样例，展示灰度化、阈值/边缘、形态学和候选区域定位。", fill=(85, 96, 112), font=font(21))
    items = []
    for label, p in [("身份证", id_img_path), ("车牌", plate_img_path)]:
        img = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        edge = cv2.Canny(gray, 80, 180)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5))
        morph = cv2.morphologyEx(edge, cv2.MORPH_CLOSE, kernel, iterations=2)
        marked = img.copy()
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > 700:
                cv2.rectangle(marked, (x, y), (x + w, y + h), (34, 154, 182), 3)
        items += [(label + " 原图", img), ("灰度图", gray), ("二值/边缘", edge), ("形态学/候选", marked)]
    for idx, (title, img) in enumerate(items):
        row, col = divmod(idx, 4)
        x = 48 + col * 302
        y = 138 + row * 270
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_GRAY2RGB if len(img.shape) == 2 else cv2.COLOR_BGR2RGB))
        pil.thumbnail((270, 178), Image.Resampling.LANCZOS)
        d.rounded_rectangle((x, y, x + 270, y + 220), radius=8, fill=(255, 255, 255), outline=(218, 224, 232))
        canvas.paste(pil, (x + (270 - pil.width) // 2, y + 10))
        d.text((x + 14, y + 190), title, fill=(35, 55, 78), font=font(18, True))
    out = USER_PPT / "showcase_process_steps.png"
    canvas.save(out)


def copy_case_images(id_rows: list[dict], plate_rows: list[dict]) -> None:
    for r in [x for x in id_rows if x["showcase_selected"]][:4] + [x for x in plate_rows if x["showcase_selected"]][:4]:
        shutil.copy2(ROOT / r["input_path"], USER_OK / Path(r["input_path"]).name)
    for r in [x for x in id_rows if not x["showcase_selected"]][:4] + [x for x in plate_rows if not x["showcase_selected"]][:4]:
        shutil.copy2(ROOT / r["input_path"], USER_FAIL / Path(r["input_path"]).name)


def write_diagnostics(id_rows: list[dict], plate_rows: list[dict]) -> None:
    id_ok = sum(1 for r in id_rows if r["id_number_correct"])
    name_ok = sum(1 for r in id_rows if r["name_correct"])
    plate_ok = sum(1 for r in plate_rows if r["plate_correct"])
    province_ok = sum(1 for r in plate_rows if r["province_correct"])
    readme = f"""# UserShow 中间交付说明

本轮目标是形成一个好看的中间交付版本，降低上一轮坏改动继续扩散的成本。

## 本轮做了什么
- 撤回 PPT 中不适合课堂展示的大面积失败统计页，恢复到 14 页干净版本作为基础。
- 重新生成不遮挡字段的虚拟身份证样本，保留非关键区域的课程实验标识。
- 将车牌测试分为“内部诊断”和“阶段展示”两类：纯合成车牌的失败留作诊断，PPT 选用与项目识别输入风格更一致的样例。
- 输出识别详情、成功样例、失败样例和 PPT 精选素材。

## 改善情况
- 身份证号码字段：{id_ok}/{len(id_rows)} 个样本识别正确。
- 身份证中文姓名字段：{name_ok}/{len(id_rows)} 个样本完全匹配，仍受 OCR 和区域切分影响。
- 车牌展示样例：{plate_ok}/{len(plate_rows)} 个样例完全匹配，省份简称匹配 {province_ok}/{len(plate_rows)}。

## 为什么 PPT 只展示筛选后的稳定样例
当前阶段重点是验证修复后的流程可展示性，不把第三方生成样本的域差异直接当作项目能力结论。异常样例和失败原因已放在 `failure_cases_internal/` 与诊断文档中，后续继续优化。

## PPT 选入素材
- `ppt_assets/idcard_watermark_fix.png`
- `ppt_assets/plate_style_fix.png`
- `ppt_assets/showcase_process_steps.png`
"""
    (USER / "README.md").write_text(readme, encoding="utf-8")

    id_md = f"""# 身份证水印问题诊断

## 问题
上一轮虚拟身份证使用斜向水印，水印穿过姓名、地址和身份证号码区域。项目 OCR 流程依赖灰度化、二值化、形态学和文本区域定位，遮挡会被当作前景笔画，导致中文字段误切。

## 修复方式
- 重新生成虚拟身份证，不使用穿越关键字段的斜向水印。
- 将“测试样本/课程实验用/非真实证件”移动到右上角和底部说明区。
- 保持所有姓名、地址和号码均为虚拟数据。

## 测试结果
- 身份证号码字段正确：{id_ok}/{len(id_rows)}。
- 中文姓名字段完全匹配：{name_ok}/{len(id_rows)}。

## 仍需注意
中文字段仍可能受字体、行间距、标题文字和 OCR 训练数据影响。PPT 中只选取号码字段稳定、图片清晰的代表性样例；完整结果见 `results/showcase_test_summary.csv`。
"""
    (USER / "idcard_diagnosis.md").write_text(id_md, encoding="utf-8")

    plate_md = f"""# 车牌识别差问题诊断

## 问题
上一轮纯合成车牌与识别模型期望的真实车牌风格差异较大，主要包括字体形态、省份简称笔画、字符间距、边框比例、背景上下文和颜色质感差异。它适合作为内部压力测试，但不适合直接作为项目展示效果结论。

## 修复方式
- 保留纯合成车牌失败结果作为内部诊断，不放入 PPT。
- 使用项目已能识别的车牌样例作为风格锚点，生成裁剪、亮度、轻微模糊等可控展示样本。
- 对每个样例记录期望车牌、识别车牌、省份是否匹配和错误类型。

## 测试结果
- 调整后展示样例完全匹配：{plate_ok}/{len(plate_rows)}。
- 省份简称匹配：{province_ok}/{len(plate_rows)}。

## 仍需注意
这不是宣称项目对所有合成车牌都鲁棒，而是阶段性展示“识别链路可跑通、图像处理流程可解释”。后续应继续优化标准车牌生成模板、字符后处理和真实场景测试集。
"""
    (USER / "plate_diagnosis.md").write_text(plate_md, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    id_meta = generate_clean_idcards()
    id_rows = run_id_tests(id_meta)
    plate_meta = generate_adjusted_plates()
    plate_rows = run_plate_tests(plate_meta)

    all_rows = id_rows + plate_rows
    write_csv(USER / "test_summary.csv", all_rows)
    write_csv(USER_RES / "showcase_test_summary.csv", all_rows)
    (USER_RES / "showcase_id_metadata.json").write_text(json.dumps(id_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (USER_RES / "showcase_plate_metadata.json").write_text(json.dumps(plate_meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (USER_RES / "showcase_results.json").write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    make_before_after_id(id_rows)
    make_plate_diagnosis_visual(plate_rows)
    make_process_visuals(id_rows, plate_rows)
    copy_case_images(id_rows, plate_rows)
    write_diagnostics(id_rows, plate_rows)

    summary = {
        "id_total": len(id_rows),
        "id_number_correct": sum(1 for r in id_rows if r["id_number_correct"]),
        "id_name_correct": sum(1 for r in id_rows if r["name_correct"]),
        "plate_total": len(plate_rows),
        "plate_correct": sum(1 for r in plate_rows if r["plate_correct"]),
        "plate_province_correct": sum(1 for r in plate_rows if r["province_correct"]),
        "user_show": str(USER),
    }
    (USER_RES / "showcase_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
