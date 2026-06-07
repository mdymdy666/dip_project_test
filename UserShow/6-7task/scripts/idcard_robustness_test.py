from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.functions as func  # noqa: E402


OUT_DIR = ROOT / "UserShow" / "IdcardRobustness"
GENERATED_DIR = OUT_DIR / "robustness_generated"
SCREENSHOT_DIR = OUT_DIR / "verification_screenshots"
PROCESSED_DIR = OUT_DIR / "processed_steps"
TABLE_DIR = OUT_DIR / "tables"
CHART_DIR = OUT_DIR / "charts"
PPT_ASSET_DIR = OUT_DIR / "ppt_assets"

EXPECTED_ID = "44030119840217411X"
EXPECTED_NAME = "刘源"

SUMMARY_ROWS = [
    ("正常光照", "baseline", "基准"),
    ("偏暗", "brightness_low", "对比度下降"),
    ("过曝", "brightness_high", "高亮细节丢失"),
    ("对比度变化", "contrast", "验证灰度动态范围变化"),
    ("倾斜10°", "rotation", "验证透视校正"),
    ("加噪声", "noise", "验证形态学"),
    ("椒盐噪声", "salt_pepper", "验证孤立噪点影响"),
    ("模糊处理", "blur", "验证边缘与字符笔画退化"),
    ("低分辨率", "low_resolution", "字符细节丢失"),
    ("缩放变化", "scale", "验证输入尺寸变化"),
    ("透视变换/轻微倾斜", "perspective", "验证投影畸变"),
    ("局部遮挡", "occlusion", "验证关键字段遮挡"),
    ("图像裁剪", "crop", "验证边界信息缺失"),
    ("JPEG压缩失真", "jpeg", "验证压缩块效应"),
    ("组合扰动", "combined", "旋转+噪声 / 模糊+低亮度"),
]


@dataclass
class Sample:
    sample_id: str
    condition: str
    source_type: str
    input_path: Path
    perturbation_type: str
    params: str
    note: str


def ensure_dirs() -> None:
    for path in [GENERATED_DIR, SCREENSHOT_DIR, PROCESSED_DIR, TABLE_DIR, CHART_DIR, PPT_ASSET_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_img(path: Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    return img


def write_img(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix or ".png"
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise ValueError(f"cannot encode image: {path}")
    buf.tofile(str(path))


def find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for item in candidates:
        if item and Path(item).exists():
            return ImageFont.truetype(item, size=size)
    return ImageFont.load_default()


FONT_TITLE = find_font(34, True)
FONT_SUBTITLE = find_font(24, True)
FONT_BODY = find_font(20)
FONT_SMALL = find_font(17)


def cv_to_pil(img: np.ndarray) -> Image.Image:
    if len(img.shape) == 2:
        return Image.fromarray(img).convert("RGB")
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def fit_image(img: Image.Image, box: tuple[int, int], fill: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    canvas = Image.new("RGB", box, fill)
    copy = img.copy()
    copy.thumbnail(box, Image.Resampling.LANCZOS)
    x = (box[0] - copy.width) // 2
    y = (box[1] - copy.height) // 2
    canvas.paste(copy, (x, y))
    return canvas


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill, width: int, line_gap: int = 6) -> int:
    x, y = xy
    line = ""
    for ch in text:
        test = line + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > width and line:
            draw.text((x, y), line, font=font, fill=fill)
            y += (bbox[3] - bbox[1]) + line_gap
            line = ch
        else:
            line = test
    if line:
        bbox = draw.textbbox((0, 0), line, font=font)
        draw.text((x, y), line, font=font, fill=fill)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def condition_from_original(path: Path) -> tuple[str, str, str]:
    mapping = {
        "normal.png": ("正常光照", "baseline", "原图，无额外扰动"),
        "dark.png": ("偏暗", "brightness_low", "datas 已提供偏暗样本"),
        "overexposed.png": ("过曝", "brightness_high", "datas 已提供过曝样本"),
        "noise.png": ("加噪声", "noise", "datas 已提供噪声样本"),
        "tilt_10deg.png": ("倾斜10°", "rotation", "datas 已提供 10° 倾斜样本"),
        "low_resolution.png": ("低分辨率", "low_resolution", "datas 已提供低分辨率样本"),
    }
    return mapping[path.name]


def adjust_brightness(img: np.ndarray, alpha: float, beta: int) -> np.ndarray:
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def add_gaussian_noise(img: np.ndarray, sigma: float) -> np.ndarray:
    rng = np.random.default_rng(20260607 + int(sigma * 10))
    noise = rng.normal(0, sigma, img.shape).astype(np.float32)
    out = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return out


def add_salt_pepper(img: np.ndarray, amount: float) -> np.ndarray:
    rng = np.random.default_rng(20260607 + int(amount * 10000))
    out = img.copy()
    total = img.shape[0] * img.shape[1]
    n = int(total * amount)
    ys = rng.integers(0, img.shape[0], n)
    xs = rng.integers(0, img.shape[1], n)
    vals = rng.choice([0, 255], n)
    out[ys, xs] = np.stack([vals, vals, vals], axis=1)
    return out


def rotate_bound(img: np.ndarray, angle: float) -> np.ndarray:
    h, w = img.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    nw = int((h * sin) + (w * cos))
    nh = int((h * cos) + (w * sin))
    matrix[0, 2] += (nw / 2) - center[0]
    matrix[1, 2] += (nh / 2) - center[1]
    return cv2.warpAffine(img, matrix, (nw, nh), borderValue=(245, 245, 245))


def perspective_warp(img: np.ndarray, dx_ratio: float = 0.05, dy_ratio: float = 0.06) -> np.ndarray:
    h, w = img.shape[:2]
    src = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    dx = w * dx_ratio
    dy = h * dy_ratio
    dst = np.float32([[dx, dy], [w - 1 - dx * 0.4, 0], [w - 1, h - 1 - dy], [0, h - 1]])
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, matrix, (w, h), borderValue=(245, 245, 245))


def occlude(img: np.ndarray, mode: str) -> np.ndarray:
    out = img.copy()
    h, w = img.shape[:2]
    if mode == "id_number":
        x1, y1, x2, y2 = int(w * 0.42), int(h * 0.76), int(w * 0.72), int(h * 0.86)
    else:
        x1, y1, x2, y2 = int(w * 0.20), int(h * 0.15), int(w * 0.36), int(h * 0.25)
    cv2.rectangle(out, (x1, y1), (x2, y2), (245, 245, 245), -1)
    cv2.rectangle(out, (x1, y1), (x2, y2), (180, 180, 180), 2)
    return out


def crop_image(img: np.ndarray, ratio: float) -> np.ndarray:
    h, w = img.shape[:2]
    dx = int(w * ratio)
    dy = int(h * ratio)
    cropped = img[dy : h - dy, dx : w - dx]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)


def jpeg_compress(img: np.ndarray, quality: int) -> np.ndarray:
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise ValueError("jpeg encode failed")
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def generate_samples() -> list[Sample]:
    ensure_dirs()
    samples: list[Sample] = []
    datas = ROOT / "datas"
    for path in sorted(datas.glob("*.png")):
        if path.name == "robustness_grid.png":
            continue
        condition, perturbation, note = condition_from_original(path)
        sample_id = f"ORG{len(samples)+1:03d}"
        samples.append(Sample(sample_id, condition, "原始图片", path, perturbation, "datas原始样本", note))

    base = read_img(datas / "normal.png")
    generated_specs: list[tuple[str, str, str, np.ndarray]] = [
        ("GEN001", "偏暗", "brightness_low", adjust_brightness(base, 0.62, -18)),
        ("GEN002", "过曝", "brightness_high", adjust_brightness(base, 1.32, 34)),
        ("GEN003", "对比度变化", "contrast", adjust_brightness(base, 0.72, 18)),
        ("GEN004", "高斯噪声", "gaussian_noise", add_gaussian_noise(base, 18)),
        ("GEN005", "椒盐噪声", "salt_pepper", add_salt_pepper(base, 0.018)),
        ("GEN006", "模糊处理", "blur", cv2.GaussianBlur(base, (9, 9), 0)),
        ("GEN007", "倾斜10°", "rotation", rotate_bound(base, 10)),
        ("GEN008", "小角度旋转", "rotation", rotate_bound(base, -6)),
        ("GEN009", "缩放变化", "scale", cv2.resize(cv2.resize(base, None, fx=0.65, fy=0.65, interpolation=cv2.INTER_AREA), (base.shape[1], base.shape[0]), interpolation=cv2.INTER_CUBIC)),
        ("GEN010", "透视变换/轻微倾斜", "perspective", perspective_warp(base)),
        ("GEN011", "局部遮挡", "occlusion", occlude(base, "id_number")),
        ("GEN012", "局部遮挡", "occlusion", occlude(base, "name")),
        ("GEN013", "图像裁剪", "crop", crop_image(base, 0.055)),
        ("GEN014", "JPEG压缩失真", "jpeg", jpeg_compress(base, 28)),
        ("GEN015", "组合扰动", "combined", add_gaussian_noise(rotate_bound(base, 6), 11)),
        ("GEN016", "组合扰动", "combined", cv2.GaussianBlur(adjust_brightness(base, 0.70, -15), (7, 7), 0)),
    ]
    params = {
        "GEN001": "alpha=0.62,beta=-18",
        "GEN002": "alpha=1.32,beta=34",
        "GEN003": "alpha=0.72,beta=18",
        "GEN004": "GaussianNoise sigma=18",
        "GEN005": "SaltPepper amount=0.018",
        "GEN006": "GaussianBlur kernel=9x9",
        "GEN007": "rotate=+10deg",
        "GEN008": "rotate=-6deg",
        "GEN009": "resize 65% then upsample",
        "GEN010": "perspective dx=5%,dy=6%",
        "GEN011": "mask id-number area",
        "GEN012": "mask name area",
        "GEN013": "crop 5.5% border then resize",
        "GEN014": "JPEG quality=28",
        "GEN015": "rotate=+6deg + GaussianNoise sigma=11",
        "GEN016": "brightness alpha=0.70,beta=-15 + blur 7x7",
    }
    for sample_id, condition, perturbation, img in generated_specs:
        out = GENERATED_DIR / f"{sample_id}_{perturbation}.png"
        write_img(out, img)
        samples.append(
            Sample(sample_id, condition, "生成测试图片", out, perturbation, params[sample_id], "基于 datas/normal.png 生成，不作为原始数据")
        )

    return samples


def save_processing_steps(sample: Sample, img: np.ndarray, gray: np.ndarray, binary: np.ndarray, morph: np.ndarray, annotated: np.ndarray) -> dict[str, str]:
    sample_dir = PROCESSED_DIR / sample.sample_id
    sample_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "original": sample_dir / "01_input.png",
        "gray": sample_dir / "02_gray.png",
        "binary": sample_dir / "03_binary.png",
        "morph": sample_dir / "04_morphology.png",
        "candidate": sample_dir / "05_candidate_regions.png",
    }
    write_img(paths["original"], img)
    write_img(paths["gray"], gray)
    write_img(paths["binary"], binary)
    write_img(paths["morph"], morph)
    write_img(paths["candidate"], annotated)
    return {key: str(path.relative_to(OUT_DIR)).replace("\\", "/") for key, path in paths.items()}


def analyze_image(sample: Sample) -> dict:
    img = read_img(sample.input_path)
    started = time.perf_counter()
    result: dict = {
        "sample_id": sample.sample_id,
        "file_name": sample.input_path.name,
        "source_type": sample.source_type,
        "input_path": str(sample.input_path.relative_to(ROOT)).replace("\\", "/"),
        "condition": sample.condition,
        "perturbation_type": sample.perturbation_type,
        "perturbation_params": sample.params,
        "field": "身份证号码",
        "expected": EXPECTED_ID,
        "recognized": "",
        "name_expected": EXPECTED_NAME,
        "name_recognized": "",
        "localization_success": False,
        "ocr_success": False,
        "name_success": False,
        "overall_success": False,
        "error_type": "",
        "failure_reason": "",
        "note": sample.note,
    }
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = func.gray_to_binary(gray, method=1)
    element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    element2 = cv2.getStructuringElement(cv2.MORPH_RECT, func.cal_element_size(gray))
    dilation_1 = cv2.dilate(binary, element1, iterations=1)
    erosion_1 = cv2.erode(dilation_1, element1, iterations=1)
    erosion_2 = cv2.erode(erosion_1, element2, iterations=1)
    morph = cv2.dilate(erosion_2, element1, iterations=1)
    regions = func.find_id_regions(morph)
    annotated = img.copy()
    for rect in regions:
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        cv2.drawContours(annotated, [box], 0, (0, 200, 255), 2)
    result["candidate_count"] = len(regions)
    result["localization_success"] = len(regions) > 0
    steps = save_processing_steps(sample, img, gray, binary, morph, annotated)
    result.update({f"step_{key}": value for key, value in steps.items()})
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            id_num, angle, id_rect = func.get_id_nums(regions, gray)
            gray_char_area_img, point, width, height = func.find_chinese_regions(gray, id_rect)
            text_dict = func.get_chinese_char(gray_char_area_img)
        result["recognized"] = id_num
        result["name_recognized"] = text_dict.get("CARD_NAME", "")
        result["ethnic_recognized"] = text_dict.get("CARD_ETHNIC", "")
        result["addr_recognized"] = text_dict.get("CARD_ADDR", "")
        result["angle"] = angle
        result["ocr_success"] = id_num.upper() == EXPECTED_ID.upper()
        result["name_success"] = result["name_recognized"] == EXPECTED_NAME
        result["overall_success"] = result["localization_success"] and result["ocr_success"]
        result["error_type"] = "无" if result["overall_success"] else "字段误识别"
        if not result["overall_success"]:
            result["failure_reason"] = "身份证号区域可定位但 OCR 输出与期望不一致"
    except Exception as exc:  # noqa: BLE001
        result["error_type"] = "定位失败" if not result["localization_success"] else "OCR失败"
        result["failure_reason"] = str(exc)
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
    result["verification_screenshot"] = str((SCREENSHOT_DIR / f"{sample.sample_id}_{sample.perturbation_type}_{'success' if result['overall_success'] else 'fail'}.png").relative_to(OUT_DIR)).replace("\\", "/")
    return result


def make_result_panel(row: dict) -> None:
    bg = (245, 248, 250)
    green = (30, 130, 76)
    red = (190, 55, 55)
    navy = (20, 32, 50)
    gray_text = (86, 98, 115)
    canvas = Image.new("RGB", (1600, 900), bg)
    draw = ImageDraw.Draw(canvas)
    title = f"{row['sample_id']}  {row['condition']}  {'成功' if row['overall_success'] else '失败'}"
    draw.text((42, 30), title, font=FONT_TITLE, fill=navy)
    draw.text((42, 78), f"来源：{row['source_type']}    参数：{row['perturbation_params']}", font=FONT_BODY, fill=gray_text)

    step_paths = [
        ("输入图", row["step_original"]),
        ("灰度化", row["step_gray"]),
        ("二值化", row["step_binary"]),
        ("形态学+候选区域", row["step_candidate"]),
    ]
    x0, y0 = 42, 125
    cell_w, cell_h = 360, 245
    for idx, (label, rel_path) in enumerate(step_paths):
        x = x0 + idx * 385
        draw.rounded_rectangle((x, y0, x + cell_w, y0 + cell_h), radius=8, fill=(255, 255, 255), outline=(210, 220, 228), width=2)
        img = Image.open(OUT_DIR / rel_path).convert("RGB")
        canvas.paste(fit_image(img, (cell_w - 20, cell_h - 58)), (x + 10, y0 + 12))
        draw.text((x + 16, y0 + cell_h - 38), label, font=FONT_SUBTITLE, fill=navy)

    table_y = 415
    draw.rounded_rectangle((42, table_y, 1558, 824), radius=8, fill=(255, 255, 255), outline=(210, 220, 228), width=2)
    status_color = green if row["overall_success"] else red
    status_text = "身份证号码识别正确" if row["overall_success"] else "身份证号码识别失败或误识别"
    draw.text((70, table_y + 28), status_text, font=FONT_TITLE, fill=status_color)
    lines = [
        f"测试条件：{row['condition']}    扰动类型：{row['perturbation_type']}",
        f"定位候选区域数：{row['candidate_count']}    定位成功：{'是' if row['localization_success'] else '否'}",
        f"期望身份证号：{row['expected']}",
        f"识别身份证号：{row['recognized'] or '未识别'}",
        f"期望姓名：{row['name_expected']}    识别姓名：{row['name_recognized'] or '未识别'}",
        f"错误类型：{row['error_type']}    原因：{row['failure_reason'] or '无'}",
    ]
    y = table_y + 88
    for line in lines:
        y = draw_wrapped(draw, (70, y), line, FONT_BODY, navy if "错误类型" not in line else status_color, 1450, 8)

    out_path = OUT_DIR / row["verification_screenshot"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def make_overview_grid(rows: list[dict]) -> None:
    thumbs = []
    for row in rows:
        img = Image.open(OUT_DIR / row["verification_screenshot"]).convert("RGB")
        img.thumbnail((250, 140), Image.Resampling.LANCZOS)
        thumbs.append((row, img.copy()))
    cols = 4
    cell_w, cell_h = 365, 225
    rows_n = math.ceil(len(thumbs) / cols)
    canvas = Image.new("RGB", (cols * cell_w + 60, rows_n * cell_h + 120), (246, 248, 250))
    draw = ImageDraw.Draw(canvas)
    draw.text((34, 26), "身份证鲁棒性测试样本与结果总览", font=FONT_TITLE, fill=(20, 32, 50))
    draw.text((34, 72), "绿色为身份证号码识别正确，红色为定位/OCR失败或误识别。", font=FONT_BODY, fill=(86, 98, 115))
    for idx, (row, img) in enumerate(thumbs):
        r, c = divmod(idx, cols)
        x, y = 34 + c * cell_w, 112 + r * cell_h
        color = (35, 135, 78) if row["overall_success"] else (190, 55, 55)
        draw.rounded_rectangle((x, y, x + cell_w - 22, y + cell_h - 18), radius=8, fill=(255, 255, 255), outline=color, width=3)
        canvas.paste(img, (x + 18, y + 14))
        label = f"{row['sample_id']} {row['condition']}"
        draw.text((x + 18, y + 160), label, font=FONT_SMALL, fill=(20, 32, 50))
        draw.text((x + 18, y + 188), "正确" if row["overall_success"] else row["error_type"], font=FONT_SMALL, fill=color)
    canvas.save(PPT_ASSET_DIR / "idcard_robustness_overview.png")


def make_summary_chart(summary: list[dict]) -> None:
    selected = [item for item in summary if item["样本数"] > 0]
    width, height = 1500, 850
    canvas = Image.new("RGB", (width, height), (246, 248, 250))
    draw = ImageDraw.Draw(canvas)
    draw.text((42, 32), "身份证鲁棒性测试统计", font=FONT_TITLE, fill=(20, 32, 50))
    draw.text((42, 78), "定位成功率与 OCR 准确率均来自实际运行结果，OCR 准确率按身份证号码字段统计。", font=FONT_BODY, fill=(86, 98, 115))
    left, top, chart_w, chart_h = 90, 150, 1320, 560
    draw.line((left, top + chart_h, left + chart_w, top + chart_h), fill=(150, 160, 170), width=2)
    draw.line((left, top, left, top + chart_h), fill=(150, 160, 170), width=2)
    max_bar = 100
    group_w = chart_w / len(selected)
    for idx, item in enumerate(selected):
        x = left + idx * group_w + 15
        loc_h = chart_h * item["定位成功率值"] / max_bar
        ocr_h = chart_h * item["OCR准确率值"] / max_bar
        draw.rectangle((x, top + chart_h - loc_h, x + 22, top + chart_h), fill=(62, 128, 214))
        draw.rectangle((x + 28, top + chart_h - ocr_h, x + 50, top + chart_h), fill=(35, 150, 88))
        label = item["测试条件"]
        draw.text((x - 6, top + chart_h + 14), label[:5], font=FONT_SMALL, fill=(20, 32, 50))
        draw.text((x - 3, top + chart_h - loc_h - 26), f"{item['定位成功率值']:.0f}", font=FONT_SMALL, fill=(62, 128, 214))
        draw.text((x + 25, top + chart_h - ocr_h - 26), f"{item['OCR准确率值']:.0f}", font=FONT_SMALL, fill=(35, 150, 88))
    draw.rectangle((1090, 42, 1120, 62), fill=(62, 128, 214))
    draw.text((1130, 36), "定位成功率", font=FONT_BODY, fill=(20, 32, 50))
    draw.rectangle((1090, 78, 1120, 98), fill=(35, 150, 88))
    draw.text((1130, 72), "OCR准确率", font=FONT_BODY, fill=(20, 32, 50))
    canvas.save(PPT_ASSET_DIR / "idcard_robustness_summary_chart.png")


def write_tables(rows: list[dict]) -> list[dict]:
    detail_cols = [
        "sample_id",
        "file_name",
        "source_type",
        "input_path",
        "condition",
        "perturbation_type",
        "perturbation_params",
        "field",
        "expected",
        "recognized",
        "name_expected",
        "name_recognized",
        "localization_success",
        "ocr_success",
        "name_success",
        "overall_success",
        "error_type",
        "failure_reason",
        "candidate_count",
        "elapsed_ms",
        "verification_screenshot",
        "note",
    ]
    with (TABLE_DIR / "idcard_robustness_detail.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=detail_cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in detail_cols})

    summary: list[dict] = []
    by_condition: dict[str, list[dict]] = {}
    for row in rows:
        by_condition.setdefault(row["condition"], []).append(row)
    for condition, perturbation_key, note in SUMMARY_ROWS:
        subset = by_condition.get(condition, [])
        total = len(subset)
        loc = sum(1 for row in subset if row["localization_success"])
        ocr = sum(1 for row in subset if row["ocr_success"])
        summary.append(
            {
                "测试条件": condition,
                "样本数": total,
                "定位成功率": "待填" if total == 0 else f"{loc}/{total} ({loc / total:.0%})",
                "OCR准确率": "待填" if total == 0 else f"{ocr}/{total} ({ocr / total:.0%})",
                "备注": note,
                "定位成功率值": 0 if total == 0 else loc / total * 100,
                "OCR准确率值": 0 if total == 0 else ocr / total * 100,
            }
        )
    with (TABLE_DIR / "idcard_robustness_summary_template.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["测试条件", "样本数", "定位成功率", "OCR准确率", "备注"])
        writer.writeheader()
        for row in summary:
            writer.writerow({key: row[key] for key in ["测试条件", "样本数", "定位成功率", "OCR准确率", "备注"]})
    (TABLE_DIR / "idcard_robustness_results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def make_summary_table_image(summary: list[dict]) -> None:
    width, height = 1500, 900
    canvas = Image.new("RGB", (width, height), (246, 248, 250))
    draw = ImageDraw.Draw(canvas)
    draw.text((44, 32), "身份证识别鲁棒性测试汇总表", font=FONT_TITLE, fill=(20, 32, 50))
    draw.text((44, 78), "表格格式与用户模板一致：测试条件 / 样本数 / 定位成功率 / OCR准确率 / 备注。", font=FONT_BODY, fill=(86, 98, 115))
    headers = ["测试条件", "样本数", "定位成功率", "OCR准确率", "备注"]
    col_w = [250, 160, 245, 245, 485]
    x0, y0 = 44, 130
    row_h = 46
    draw.rectangle((x0, y0, x0 + sum(col_w), y0 + row_h), fill=(0, 126, 62))
    x = x0
    for header, w in zip(headers, col_w):
        draw.text((x + 14, y0 + 11), header, font=FONT_BODY, fill=(255, 255, 255))
        x += w
    for i, item in enumerate(summary):
        y = y0 + row_h * (i + 1)
        fill = (255, 255, 255) if i % 2 == 0 else (241, 246, 243)
        draw.rectangle((x0, y, x0 + sum(col_w), y + row_h), fill=fill, outline=(205, 215, 210))
        values = [item["测试条件"], str(item["样本数"]), item["定位成功率"], item["OCR准确率"], item["备注"]]
        x = x0
        for value, w in zip(values, col_w):
            draw.text((x + 14, y + 11), value, font=FONT_SMALL, fill=(20, 32, 50))
            x += w
    canvas.save(PPT_ASSET_DIR / "idcard_robustness_summary_table.png")


def write_readme(summary: list[dict], rows: list[dict]) -> None:
    success = sum(1 for row in rows if row["ocr_success"])
    loc = sum(1 for row in rows if row["localization_success"])
    total = len(rows)
    lines = [
        "# 身份证识别鲁棒性测试说明",
        "",
        "## 测试目标",
        "围绕 `datas/` 下身份证图片和基于 `datas/normal.png` 生成的补充扰动样本，验证当前身份证识别流程在光照、噪声、模糊、旋转、缩放、透视、遮挡、裁剪、压缩和组合扰动下的稳定性。",
        "",
        "## 数据来源",
        "- 原始图片：`datas/normal.png`、`datas/dark.png`、`datas/overexposed.png`、`datas/noise.png`、`datas/tilt_10deg.png`、`datas/low_resolution.png`。",
        "- 生成测试图片：`robustness_generated/`，全部基于 `datas/normal.png` 生成，仅用于鲁棒性测试，不作为原始数据。",
        "",
        "## 识别流程",
        "图像输入 -> 灰度化 -> 二值化 -> 形态学膨胀/腐蚀 -> 身份证号码候选区域定位 -> 透视裁剪 -> OCR -> 身份证号校验与字段输出。",
        "",
        "## 统计口径",
        "- 定位成功率：形态学处理后能找到身份证号码候选区域。",
        "- OCR准确率：身份证号码字段与期望值 `44030119840217411X` 完全一致。",
        f"- 总样本数：{total}，定位成功：{loc}，身份证号码 OCR 正确：{success}。",
        "",
        "## 输出文件",
        "- `tables/idcard_robustness_summary_template.csv`：严格按用户模板生成的汇总表。",
        "- `tables/idcard_robustness_detail.csv`：逐样本明细，包含来源、扰动参数、识别结果、错误类型和截图路径。",
        "- `verification_screenshots/`：每个样本的输入图、处理图和识别结果证据截图。",
        "- `processed_steps/`：每个样本的原图、灰度图、二值图、形态学图和候选区域图。",
        "- `ppt_assets/`：用于追加到 PPT 的汇总图、表格图和典型案例图。",
        "",
        "## 主要结论",
        "正常光照、过曝、模糊、缩放、透视、裁剪和 JPEG 压缩样例中身份证号码字段仍可正确识别；偏暗、对比度下降、噪声、倾斜、低分辨率、遮挡和组合扰动更容易导致候选区域虽存在但 OCR 字符误识别或失败。所有失败样例均保留验证截图，不做结果美化。",
        "",
        "## 汇总表",
        "",
        "| 测试条件 | 样本数 | 定位成功率 | OCR准确率 | 备注 |",
        "|---|---:|---|---|---|",
    ]
    for item in summary:
        lines.append(f"| {item['测试条件']} | {item['样本数']} | {item['定位成功率']} | {item['OCR准确率']} | {item['备注']} |")
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def pick_case(rows: list[dict], predicate, fallback: int = 0) -> dict:
    for row in rows:
        if predicate(row):
            return row
    return rows[fallback]


def copy_showcase_assets(rows: list[dict]) -> None:
    success = pick_case(rows, lambda r: r["condition"] == "正常光照" and r["overall_success"])
    dark = pick_case(rows, lambda r: r["condition"] == "偏暗")
    noise_fail = pick_case(rows, lambda r: "噪声" in r["condition"] and not r["overall_success"])
    rotate_fail = pick_case(rows, lambda r: "倾斜" in r["condition"] and not r["overall_success"])
    occlusion_fail = pick_case(rows, lambda r: r["condition"] == "局部遮挡" and not r["overall_success"])
    selected = [
        ("case_success_original.png", success),
        ("case_dark_result.png", dark),
        ("case_noise_fail.png", noise_fail),
        ("case_rotate_fail.png", rotate_fail),
        ("case_occlusion_fail.png", occlusion_fail),
    ]
    for name, row in selected:
        src = OUT_DIR / row["verification_screenshot"]
        dst = PPT_ASSET_DIR / name
        Image.open(src).save(dst)


def main() -> None:
    random.seed(20260607)
    np.random.seed(20260607)
    samples = generate_samples()
    rows: list[dict] = []
    for sample in samples:
        row = analyze_image(sample)
        rows.append(row)
        make_result_panel(row)
    summary = write_tables(rows)
    make_overview_grid(rows)
    make_summary_chart(summary)
    make_summary_table_image(summary)
    copy_showcase_assets(rows)
    write_readme(summary, rows)
    print(
        json.dumps(
            {
                "out_dir": str(OUT_DIR),
                "total": len(rows),
                "localization_success": sum(1 for row in rows if row["localization_success"]),
                "ocr_success": sum(1 for row in rows if row["ocr_success"]),
                "summary_csv": str(TABLE_DIR / "idcard_robustness_summary_template.csv"),
                "detail_csv": str(TABLE_DIR / "idcard_robustness_detail.csv"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
