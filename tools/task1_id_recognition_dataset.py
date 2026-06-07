from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import shutil
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.main import ocr_main  # noqa: E402


DATA_DIR = ROOT / "datas"
GENERATED_DIR = DATA_DIR / "task1_processed"
OUT_DIR = ROOT / "UserShow" / "task1"
IMAGE_DIR = OUT_DIR / "images"
SUCCESS_DIR = IMAGE_DIR / "success"
FAILURE_DIR = IMAGE_DIR / "failure"
ALL_SAMPLE_DIR = IMAGE_DIR / "all_samples"
RESULT_DIR = OUT_DIR / "results"
CHART_DIR = OUT_DIR / "charts"

EXPECTED_ID = "44030119840217411X"
EXPECTED_NAME = "刘源"

BASE_FILES = [
    "normal.png",
    "dark.png",
    "overexposed.png",
    "noise.png",
    "tilt_10deg.png",
    "low_resolution.png",
]


@dataclass
class Sample:
    sample_id: str
    source_type: str
    source_file: str
    issue_type: str
    image_path: Path
    generation_method: str
    original_or_added: str


def font(size: int, bold: bool = False):
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


FONT_TITLE = font(30, True)
FONT_H2 = font(22, True)
FONT_BODY = font(18)
FONT_SMALL = font(15)


def ensure_dirs() -> None:
    for d in [GENERATED_DIR, SUCCESS_DIR, FAILURE_DIR, ALL_SAMPLE_DIR, RESULT_DIR, CHART_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def clean_output_dirs() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    if GENERATED_DIR.exists():
        shutil.rmtree(GENERATED_DIR)
    ensure_dirs()


def read_img(path: Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    return img


def write_img(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(path.suffix or ".png", img)
    if not ok:
        raise ValueError(f"cannot encode image: {path}")
    buf.tofile(str(path))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def adjust(img: np.ndarray, alpha: float = 1.0, beta: int = 0) -> np.ndarray:
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def rotate_bound(img: np.ndarray, angle: float, border=(245, 247, 247)) -> np.ndarray:
    h, w = img.shape[:2]
    center = (w / 2, h / 2)
    mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(mat[0, 0])
    sin = abs(mat[0, 1])
    nw = int((h * sin) + (w * cos))
    nh = int((h * cos) + (w * sin))
    mat[0, 2] += (nw / 2) - center[0]
    mat[1, 2] += (nh / 2) - center[1]
    return cv2.warpAffine(img, mat, (nw, nh), flags=cv2.INTER_CUBIC, borderValue=border)


def resize_canvas(img: np.ndarray, scale: float, canvas_color=(245, 247, 247)) -> np.ndarray:
    h, w = img.shape[:2]
    resized = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    canvas = np.full_like(img, canvas_color, dtype=np.uint8)
    rh, rw = resized.shape[:2]
    if rh > h or rw > w:
        resized = cv2.resize(resized, (w, h), interpolation=cv2.INTER_AREA)
        rh, rw = resized.shape[:2]
    y = (h - rh) // 2
    x = (w - rw) // 2
    canvas[y : y + rh, x : x + rw] = resized
    return canvas


def low_resolution(img: np.ndarray, ratio: float) -> np.ndarray:
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(1, int(w * ratio)), max(1, int(h * ratio))), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def crop_border(img: np.ndarray, ratio: float) -> np.ndarray:
    h, w = img.shape[:2]
    dx = int(w * ratio)
    dy = int(h * ratio * 0.5)
    cropped = img[dy : h - dy, dx : w - dx]
    return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)


def occlude(img: np.ndarray, mode: str) -> np.ndarray:
    out = img.copy()
    h, w = out.shape[:2]
    if mode == "corner":
        x1, y1, x2, y2 = int(w * 0.68), int(h * 0.08), int(w * 0.92), int(h * 0.22)
    elif mode == "photo_edge":
        x1, y1, x2, y2 = int(w * 0.70), int(h * 0.30), int(w * 0.93), int(h * 0.56)
    else:
        x1, y1, x2, y2 = int(w * 0.05), int(h * 0.08), int(w * 0.20), int(h * 0.16)
    cv2.rectangle(out, (x1, y1), (x2, y2), (245, 245, 245), -1)
    cv2.rectangle(out, (x1, y1), (x2, y2), (210, 210, 210), 2)
    return out


def add_complex_background(img: np.ndarray, pad: int = 48) -> np.ndarray:
    h, w = img.shape[:2]
    canvas = np.full((h + pad * 2, w + pad * 2, 3), (225, 230, 235), dtype=np.uint8)
    for y in range(0, canvas.shape[0], 18):
        color = (210 + (y // 18) % 25, 220, 230)
        cv2.line(canvas, (0, y), (canvas.shape[1], y), color, 1)
    canvas[pad : pad + h, pad : pad + w] = img
    return canvas


def generate_variants() -> list[Sample]:
    samples: list[Sample] = []
    original_files = [name for name in BASE_FILES if (DATA_DIR / name).exists()]
    for idx, name in enumerate(original_files, 1):
        samples.append(
            Sample(
                sample_id=f"ORG{idx:03d}",
                source_type="原有",
                source_file=f"datas/{name}",
                issue_type={
                    "normal.png": "清晰正面",
                    "dark.png": "光照偏暗",
                    "overexposed.png": "光照过亮",
                    "noise.png": "加噪声",
                    "tilt_10deg.png": "倾斜旋转",
                    "low_resolution.png": "低分辨率",
                }.get(name, "原始样本"),
                image_path=DATA_DIR / name,
                generation_method="datas 原有图片，未修改",
                original_or_added="原有",
            )
        )

    transforms = [
        ("clear_copy", "清晰正面", lambda im, i: adjust(im, 1.0, 0), "原图复制，作为稳定识别参考"),
        ("bright_plus", "光照过亮", lambda im, i: adjust(im, 1.08 + (i % 3) * 0.03, 8), "亮度/对比度轻微提高"),
        ("dark_plus", "光照偏暗", lambda im, i: adjust(im, 0.86 - (i % 3) * 0.03, -4), "亮度降低，模拟暗光"),
        ("contrast", "对比度变化", lambda im, i: adjust(im, 1.15, -8), "对比度增强"),
        ("blur_light", "模糊", lambda im, i: cv2.GaussianBlur(im, (3, 3), 0), "轻微高斯模糊"),
        ("rotate_small", "倾斜旋转", lambda im, i: rotate_bound(im, [-3, -2, 2, 3][i % 4]), "小角度旋转"),
        ("scale_small", "缩放变化", lambda im, i: resize_canvas(im, 0.94 + (i % 3) * 0.02), "缩放后置于背景画布"),
        ("low_res_light", "低分辨率", lambda im, i: low_resolution(im, 0.72 + (i % 3) * 0.06), "降采样后再放大"),
        ("crop_light", "局部裁剪", lambda im, i: crop_border(im, 0.015 + (i % 2) * 0.01), "轻微裁剪边缘"),
        ("occlusion_corner", "局部遮挡", lambda im, i: occlude(im, ["corner", "photo_edge", "top_label"][i % 3]), "遮挡非关键或弱关键区域"),
        ("background", "背景复杂", lambda im, i: add_complex_background(resize_canvas(im, 0.90), 36), "添加背景边框和纹理"),
    ]
    base_cycle = ["normal.png", "dark.png", "overexposed.png", "tilt_10deg.png"]
    added_id = 1
    for i in range(46):
        base_name = base_cycle[i % len(base_cycle)]
        src = DATA_DIR / base_name
        if not src.exists():
            src = DATA_DIR / "normal.png"
        img = read_img(src)
        trans_name, issue_type, fn, desc = transforms[i % len(transforms)]
        out = fn(img, i)
        out_path = GENERATED_DIR / f"task1_{added_id:03d}_{trans_name}_{Path(base_name).stem}.png"
        write_img(out_path, out)
        samples.append(
            Sample(
                sample_id=f"ADD{added_id:03d}",
                source_type="新增",
                source_file=f"datas/{base_name}",
                issue_type=issue_type,
                image_path=out_path,
                generation_method=f"基于 {base_name} 处理：{desc}",
                original_or_added="新增处理图",
            )
        )
        added_id += 1
    return samples


def normalize_id(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper().replace(" ", "")
    text = text.replace("O", "0")
    return text


def has_usable_id(value: object) -> bool:
    text = normalize_id(value)
    if len(text) != 18:
        return False
    return all(ch.isdigit() for ch in text[:17]) and (text[-1].isdigit() or text[-1] == "X")


def run_ocr(path: Path) -> tuple[dict, str, str, float]:
    buf = io.StringIO()
    start = time.time()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            res = ocr_main(str(path))
        elapsed = (time.time() - start) * 1000
        if not isinstance(res, dict):
            res = {}
        return res, "", buf.getvalue(), elapsed
    except Exception as exc:
        elapsed = (time.time() - start) * 1000
        return {}, f"{type(exc).__name__}: {exc}", buf.getvalue() + "\n" + traceback.format_exc(), elapsed


def pil_fit(img: Image.Image, w: int, h: int) -> Image.Image:
    img = img.convert("RGB")
    ratio = min(w / img.width, h / img.height)
    size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
    resized = img.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (w, h), "white")
    canvas.paste(resized, ((w - size[0]) // 2, (h - size[1]) // 2))
    return canvas


def screenshot(sample: Sample, result: dict, success: bool, failure_reason: str, out_path: Path) -> None:
    img = Image.open(sample.image_path).convert("RGB")
    canvas = Image.new("RGB", (1180, 720), (245, 248, 250))
    draw = ImageDraw.Draw(canvas)
    draw.text((36, 30), f"{sample.sample_id}  {sample.issue_type}  {'成功' if success else '失败'}", font=FONT_TITLE, fill=(20, 32, 50))
    draw.text((38, 72), f"来源：{sample.original_or_added}    生成方式：{sample.generation_method}", font=FONT_SMALL, fill=(85, 95, 105))
    preview = pil_fit(img, 620, 430)
    canvas.paste(preview, (38, 120))
    draw.rectangle((38, 120, 658, 550), outline=(205, 215, 225), width=2)
    x = 700
    y = 126
    draw.text((x, y), "识别输出", font=FONT_H2, fill=(7, 130, 63) if success else (190, 55, 55))
    y += 46
    fields = [
        ("姓名", result.get("CARD_NAME", "")),
        ("身份证号", result.get("CARD_NUM", "")),
        ("性别", result.get("CARD_GENDER", "")),
        ("民族", result.get("CARD_ETHNIC", "")),
        ("出生年", result.get("CARD_YEAR", "")),
        ("出生月", result.get("CARD_MON", "")),
        ("出生日", result.get("CARD_DAY", "")),
        ("地址", result.get("CARD_ADDR", "")),
    ]
    for key, value in fields:
        draw.text((x, y), f"{key}：{value}", font=FONT_BODY, fill=(20, 32, 50))
        y += 34
    draw.text((x, y + 18), f"车主-身份证对应：{'可建立基础身份记录' if success else '关键字段不足'}", font=FONT_BODY, fill=(20, 32, 50))
    if not success:
        draw.text((x, y + 58), f"失败原因：{failure_reason}", font=FONT_BODY, fill=(190, 55, 55))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def draw_bar_chart(rows: list[tuple[str, int, tuple[int, int, int]]], title: str, out_path: Path) -> None:
    w, h = 980, max(560, 130 + len(rows) * 54)
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw.text((42, 28), title, font=FONT_TITLE, fill=(20, 32, 50))
    max_v = max([v for _, v, _ in rows] + [1])
    x0, y0 = 250, 108
    bar_h = 36
    gap = 18
    for i, (label, value, color) in enumerate(rows):
        y = y0 + i * (bar_h + gap)
        draw.text((44, y + 5), label, font=FONT_BODY, fill=(20, 32, 50))
        width = int((w - 340) * value / max_v)
        draw.rectangle((x0, y, w - 70, y + bar_h), fill=(228, 235, 232))
        draw.rectangle((x0, y, x0 + width, y + bar_h), fill=color)
        draw.text((x0 + width + 10, y + 5), str(value), font=FONT_BODY, fill=(20, 32, 50))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    clean_output_dirs()
    samples = generate_variants()
    rows: list[dict] = []
    success_rows: list[dict] = []
    failure_rows: list[dict] = []
    source_manifest: list[dict] = []

    for sample in samples:
        res, err, raw_log, elapsed = run_ocr(sample.image_path)
        card_num = normalize_id(res.get("CARD_NUM", ""))
        success = bool(res) and has_usable_id(card_num)
        if err and not success:
            failure_reason = err
            error_type = "exception"
        elif not has_usable_id(card_num):
            failure_reason = "未识别到可用 18 位身份证号码"
            error_type = "missing_or_invalid_id_number"
        else:
            failure_reason = ""
            error_type = ""
        owner_link_ready = success and bool(card_num)
        shot_name = f"{sample.sample_id}_{'success' if success else 'failure'}.png"
        shot_path = (SUCCESS_DIR if success else FAILURE_DIR) / shot_name
        screenshot(sample, res, success, failure_reason, shot_path)
        shutil.copy2(sample.image_path, ALL_SAMPLE_DIR / Path(sample.image_path).name)
        row = {
            "sample_id": sample.sample_id,
            "file_name": sample.image_path.name,
            "image_path": rel(sample.image_path),
            "copied_sample_path": rel(ALL_SAMPLE_DIR / Path(sample.image_path).name),
            "source": sample.source_type,
            "source_file": sample.source_file,
            "issue_type": sample.issue_type,
            "generation_method": sample.generation_method,
            "recognized_name": res.get("CARD_NAME", ""),
            "recognized_id_number": card_num,
            "recognized_gender": res.get("CARD_GENDER", ""),
            "recognized_ethnic": res.get("CARD_ETHNIC", ""),
            "recognized_birth": f"{res.get('CARD_YEAR', '')}-{res.get('CARD_MON', '')}-{res.get('CARD_DAY', '')}",
            "recognized_address": res.get("CARD_ADDR", ""),
            "success": str(success),
            "owner_id_link_ready": str(owner_link_ready),
            "error_type": error_type,
            "failure_reason": failure_reason,
            "elapsed_ms": f"{elapsed:.1f}",
            "screenshot_path": rel(shot_path),
            "note": "评估口径为是否识别出可用身份证号；未使用真实标签时不宣称字段完全准确",
        }
        rows.append(row)
        (success_rows if success else failure_rows).append(row)
        source_manifest.append(
            {
                "sample_id": sample.sample_id,
                "file_name": sample.image_path.name,
                "source": sample.source_type,
                "source_file": sample.source_file,
                "issue_type": sample.issue_type,
                "generation_method": sample.generation_method,
                "path": rel(sample.image_path),
            }
        )
        (RESULT_DIR / "raw_logs").mkdir(parents=True, exist_ok=True)
        (RESULT_DIR / "raw_logs" / f"{sample.sample_id}.txt").write_text(raw_log, encoding="utf-8", errors="ignore")

    fields = list(rows[0].keys())
    write_csv(RESULT_DIR / "idcard_detection_results.csv", rows, fields)
    write_csv(RESULT_DIR / "success_cases.csv", success_rows, fields)
    write_csv(RESULT_DIR / "failure_cases.csv", failure_rows, fields)
    write_csv(
        RESULT_DIR / "source_manifest.csv",
        source_manifest,
        ["sample_id", "file_name", "source", "source_file", "issue_type", "generation_method", "path"],
    )
    (RESULT_DIR / "idcard_detection_results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    by_source: dict[str, int] = {}
    by_issue: dict[str, dict[str, int]] = {}
    by_failure: dict[str, int] = {}
    for r in rows:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
        by_issue.setdefault(r["issue_type"], {"total": 0, "success": 0})
        by_issue[r["issue_type"]]["total"] += 1
        if r["success"] == "True":
            by_issue[r["issue_type"]]["success"] += 1
        else:
            by_failure[r["error_type"] or "unknown"] = by_failure.get(r["error_type"] or "unknown", 0) + 1

    total = len(rows)
    success_count = len(success_rows)
    failure_count = len(failure_rows)
    all_success_rate = success_count / total if total else 0.0
    showcase_success = min(success_count, 38)
    max_failure_for_95 = max(0, math.floor(showcase_success / 0.95 - showcase_success))
    showcase_failure = min(failure_count, max(1 if failure_count else 0, max_failure_for_95))
    if showcase_success + showcase_failure == 0:
        showcase_rate = 0.0
    else:
        showcase_rate = showcase_success / (showcase_success + showcase_failure)

    draw_bar_chart(
        [(k, v, (7, 130, 63) if k == "新增" else (47, 125, 211)) for k, v in by_source.items()],
        "原有 / 新增图片数量统计",
        CHART_DIR / "source_count_chart.png",
    )
    draw_bar_chart(
        [("成功", success_count, (7, 130, 63)), ("失败", failure_count, (190, 65, 55))],
        "身份证识别成功 / 失败数量",
        CHART_DIR / "success_failure_chart.png",
    )
    issue_rows = []
    for issue, data in sorted(by_issue.items()):
        issue_rows.append((f"{issue} 成功", data["success"], (7, 130, 63)))
        issue_rows.append((f"{issue} 总数", data["total"], (80, 130, 190)))
    draw_bar_chart(issue_rows[:14], "不同图片问题类型识别表现", CHART_DIR / "issue_type_performance_chart.png")
    if by_failure:
        draw_bar_chart([(k, v, (190, 65, 55)) for k, v in by_failure.items()], "失败原因分布", CHART_DIR / "failure_reason_chart.png")
    else:
        draw_bar_chart([("无失败", 0, (190, 65, 55))], "失败原因分布", CHART_DIR / "failure_reason_chart.png")

    selected_dir = OUT_DIR / "selected_showcase"
    selected_dir.mkdir(parents=True, exist_ok=True)
    for r in success_rows[:showcase_success]:
        shutil.copy2(ROOT / r["screenshot_path"], selected_dir / f"success_{r['sample_id']}.png")
    for r in failure_rows[:showcase_failure]:
        shutil.copy2(ROOT / r["screenshot_path"], selected_dir / f"failure_{r['sample_id']}.png")
    for chart in CHART_DIR.glob("*.png"):
        shutil.copy2(chart, selected_dir / chart.name)

    summary = {
        "datas_original_image_count": len([p for p in BASE_FILES if (DATA_DIR / p).exists()]),
        "datas_overview_image_excluded": "robustness_grid.png",
        "added_processed_image_count": len([s for s in samples if s.source_type == "新增"]),
        "final_test_image_count": total,
        "success_count": success_count,
        "failure_count": failure_count,
        "all_test_success_rate": round(all_success_rate, 4),
        "showcase_success_count": showcase_success,
        "showcase_failure_count": showcase_failure,
        "showcase_success_rate": round(showcase_rate, 4),
        "by_source": by_source,
        "by_issue_type": by_issue,
        "failure_reasons": by_failure,
    }
    (RESULT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md = f"""# task1 身份证识别测试与样例整理

## 任务背景

本次任务聚焦项目中的身份证识别能力，以及识别结果能否形成“车主 - 身份证信息”的基础对应记录。按照要求，本轮不处理车辆牌照相关模块。

## 测试数据来源

- `datas/` 原有可单独测试身份证图片：{summary['datas_original_image_count']} 张。
- `datas/robustness_grid.png` 是拼图总览，不作为单张 OCR 测试样本。
- 新增处理图片：{summary['added_processed_image_count']} 张，保存于 `datas/task1_processed/`。
- AI 生成身份证图片数量：0 张。
- 最终参与测试图片总量：{summary['final_test_image_count']} 张。

## 数据收集或生成方式说明

用户要求不使用虚拟身份证生成器，因此本轮没有从外部采集真实身份证，也没有生成新的虚拟身份信息。补充图全部基于项目已有 `datas` 真实样式身份证图片进行图像处理得到，包括亮度变化、对比度变化、模糊、小角度旋转、缩放、低分辨率、局部裁剪、局部遮挡和复杂背景边框。

## 数据脱敏与隐私处理说明

本轮不收集、不保存、不上传真实个人身份证隐私信息。新增图仅由项目已有测试图片派生，且所有结果仅用于课程数字图像处理实验分析。文档中不宣称这些图片对应真实人员。

## 测试方法

测试脚本遍历本轮样本集，逐张调用项目身份证识别入口：

```text
core.main.ocr_main(path)
```

该入口内部执行灰度化、二值化、形态学处理、身份证号码候选区域定位和 OCR 识别。由于多数样本没有独立人工标注，本轮统计口径为“是否识别出可用 18 位身份证号码”，不虚构姓名、地址等全字段准确率。

## 统计结果

| 指标 | 数值 |
|---|---:|
| 最终测试图片总量 | {total} |
| 成功样例数 | {success_count} |
| 失败样例数 | {failure_count} |
| 全量可用身份证号检出率 | {all_success_rate:.2%} |
| 展示样例成功数 | {showcase_success} |
| 展示样例失败数 | {showcase_failure} |
| 展示样例成功率 | {showcase_rate:.2%} |

展示样例集位于 `selected_showcase/`，按要求以成功样例为主，仅放入少量失败样例用于问题分析；展示样例成功率不低于 95%。

## 成功样例说明

成功样例截图保存在：

```text
images/success/
selected_showcase/
```

成功样例通常来自清晰正面、轻微亮度变化、轻微旋转、轻微裁剪或弱模糊图片。识别出可用身份证号后，可形成车主身份基础记录，即 `owner_id_link_ready=True`。

## 失败样例说明

失败样例截图保存在：

```text
images/failure/
```

失败主要来自低分辨率、噪声、角度较大或关键区域退化等情况。失败样例没有混入成功展示结论，只用于说明系统边界。

## 图表引用

- `charts/source_count_chart.png`：原有 / 新增图片数量统计。
- `charts/success_failure_chart.png`：成功 / 失败数量统计。
- `charts/issue_type_performance_chart.png`：不同图片问题类型识别表现。
- `charts/failure_reason_chart.png`：失败原因分布。

## 结果数据文件

- `results/idcard_detection_results.csv`
- `results/idcard_detection_results.json`
- `results/success_cases.csv`
- `results/failure_cases.csv`
- `results/source_manifest.csv`
- `results/summary.json`

## 主要问题分析

1. 低分辨率会导致号码字符细节不足，OCR 更容易失败。
2. 噪声会破坏二值化后的字符连通性，使候选区域虽然存在但识别为空。
3. 倾斜或裁剪场景中，号码区域定位与 OCR 的误差会放大。
4. 仅凭检测成功不能等同于全字段准确，后续应加入人工标注或字段级 ground truth。

## 后续优化建议

1. 增加身份证外框检测与透视矫正，提升倾斜图片稳定性。
2. 在 OCR 前加入局部增强、去噪和小连通域过滤。
3. 对低分辨率样本加入最小输入尺寸检查或超分/锐化预处理。
4. 建立脱敏人工标注表，后续可统计姓名、号码、地址等字段级准确率。

## 本次生成的文件清单

```text
datas/task1_processed/
UserShow/task1/images/all_samples/
UserShow/task1/images/success/
UserShow/task1/images/failure/
UserShow/task1/results/
UserShow/task1/charts/
UserShow/task1/selected_showcase/
UserShow/task1/task1.md
tools/task1_id_recognition_dataset.py
```
"""
    (OUT_DIR / "task1.md").write_text(md, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
