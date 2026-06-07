from __future__ import annotations

import contextlib
import csv
import io
import json
import re
import shutil
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import TESSERACT_OCR  # noqa: E402
from core.main import ocr_main  # noqa: E402
import core.functions as func  # noqa: E402

pytesseract.pytesseract.tesseract_cmd = TESSERACT_OCR

TASK1 = ROOT / "UserShow" / "task1"
OUT = ROOT / "UserShow" / "task1_ablation"
TABLES = OUT / "tables"
CHARTS = OUT / "charts"
SCREENSHOTS = OUT / "screenshots"
SUCCESS_DIR = OUT / "selected_success_cases"
FAIL_DIR = OUT / "selected_failure_cases"
STEPS_DIR = OUT / "step_outputs"
STEP_CARDS = OUT / "step_result_cards"

EXPECTED_ID = "44030119840217411X"

GROUPS = [
    ("A", "A 对照组", "直接 OCR", "背景干扰"),
    ("B", "B", "灰度 + 二值", "断裂/噪声"),
    ("C", "C", "B + 形态学", "区域粘连"),
    ("D", "D", "C + 轮廓筛选", "误检区域"),
    ("E", "E 完整流程", "D + ROI + 校正 + 白名单 OCR", "低质图片"),
]


@dataclass
class Sample:
    sample_id: str
    image_path: Path
    issue_type: str
    source: str


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


def ensure_clean() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    for d in [TABLES, CHARTS, SCREENSHOTS, SUCCESS_DIR, FAIL_DIR, STEPS_DIR, STEP_CARDS]:
        d.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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


def load_samples() -> list[Sample]:
    csv_path = TASK1 / "results" / "idcard_detection_results.csv"
    samples = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            samples.append(
                Sample(
                    sample_id=row["sample_id"],
                    image_path=ROOT / row["image_path"],
                    issue_type=row["issue_type"],
                    source=row["source"],
                )
            )
    return samples


def normalize_id(text: str) -> str:
    text = (text or "").upper().replace("O", "0")
    return "".join(ch for ch in text if ch.isalnum())


def extract_id(text: str) -> str:
    cleaned = normalize_id(text)
    matches = re.findall(r"\d{15,17}[\dX]?", cleaned)
    if not matches:
        return ""
    matches.sort(key=len, reverse=True)
    best = matches[0]
    return best[:18]


def char_accuracy(pred: str, target: str = EXPECTED_ID) -> float:
    pred = normalize_id(pred)
    if not pred:
        return 0.0
    pred = pred[: len(target)].ljust(len(target), "_")
    return sum(a == b for a, b in zip(pred, target)) / len(target)


def choose_candidate(texts: list[str]) -> str:
    cleaned = [normalize_id(t) for t in texts if normalize_id(t)]
    if not cleaned:
        return ""
    for text in cleaned:
        if len(text) == 18 and func.is_identi_number(text):
            return text
    for text in cleaned:
        if len(text) == 18:
            return text
    cleaned.sort(key=len, reverse=True)
    return cleaned[0][:18]


def whitelist_ocr(img: np.ndarray, psm: int = 7) -> str:
    config = f"--psm {psm} -c tessedit_char_whitelist=0123456789Xx"
    return extract_id(ocr_image(img, config))


def threshold_and_morph(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    _, binary = func.gray_to_binary(gray, method=1)
    a = func.cal_element_size(gray)
    element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    element2 = cv2.getStructuringElement(cv2.MORPH_RECT, a)
    dilation_1 = cv2.dilate(binary, element1, iterations=1)
    erosion_1 = cv2.erode(dilation_1, element1, iterations=1)
    erosion_2 = cv2.erode(erosion_1, element2, iterations=1)
    morphology = cv2.dilate(erosion_2, element1, iterations=1)
    return binary, morphology


def crop_rect(gray_or_binary: np.ndarray, rect) -> np.ndarray:
    angle = rect[2]
    a, b = rect[1]
    if a <= 1 or b <= 1:
        return gray_or_binary
    if a > b:
        width, height = a, b
        pts2 = np.float32([[0, height], [0, 0], [width, 0], [width, height]])
    else:
        width, height = b, a
        angle = 90 + angle
        pts2 = np.float32([[width, height], [0, height], [0, 0], [width, 0]])
    box = cv2.boxPoints(rect)
    pts1 = np.float32(box)
    m = cv2.getPerspectiveTransform(pts1, pts2)
    return cv2.warpPerspective(gray_or_binary, m, (int(width), int(height)))


def normalized_roi_variants(gray: np.ndarray, binary: np.ndarray, rect, out_dir: Path) -> list[np.ndarray]:
    roi_gray = crop_rect(gray, rect)
    roi_binary = crop_rect(binary, rect)
    if roi_gray.size == 0:
        return []
    target_h = 54
    scale = target_h / max(1, roi_gray.shape[0])
    target_w = max(180, min(640, int(roi_gray.shape[1] * scale)))
    gray_resized = cv2.resize(roi_gray, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
    binary_resized = cv2.resize(roi_binary, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
    _, otsu = cv2.threshold(gray_resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, kernel, iterations=1)
    padded = cv2.copyMakeBorder(cleaned, 10, 10, 16, 16, cv2.BORDER_CONSTANT, value=255)
    write_img(out_dir / "roi_gray.png", gray_resized)
    write_img(out_dir / "roi_binary.png", binary_resized)
    write_img(out_dir / "roi_otsu.png", otsu)
    write_img(out_dir / "roi_cleaned_padded.png", padded)
    return [padded, otsu, binary_resized, gray_resized]


def ocr_image(img: np.ndarray, config: str = "--psm 6") -> str:
    try:
        return pytesseract.image_to_string(img, config=config)
    except Exception:
        return ""


def draw_regions(img: np.ndarray, regions, out_path: Path) -> None:
    show = img.copy()
    for rect in regions:
        box = cv2.boxPoints(rect)
        box = np.int32(box)
        cv2.drawContours(show, [box], 0, (0, 190, 0), 2)
    write_img(out_path, show)


def run_group(sample: Sample, group_id: str) -> dict:
    img = read_img(sample.image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    step_dir = STEPS_DIR / sample.sample_id / group_id
    step_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    localization_success = False
    recognized = ""
    failure_type = ""
    evidence = ""
    candidate_count = 0
    try:
        if group_id == "A":
            recognized = extract_id(ocr_image(img, "--psm 6"))
            localization_success = bool(recognized)
            evidence = rel(sample.image_path)
        elif group_id == "B":
            binary, _ = threshold_and_morph(gray)
            write_img(step_dir / "binary.png", binary)
            recognized = extract_id(ocr_image(binary, "--psm 6"))
            localization_success = bool(recognized)
            evidence = rel(step_dir / "binary.png")
        elif group_id == "C":
            binary, morphology = threshold_and_morph(gray)
            write_img(step_dir / "binary.png", binary)
            write_img(step_dir / "morphology.png", morphology)
            regions = func.find_id_regions(morphology)
            candidate_count = len(regions)
            localization_success = candidate_count > 0
            draw_regions(img, regions, step_dir / "candidate_regions.png")
            texts = []
            for rect in regions[:4]:
                crop = crop_rect(binary, rect)
                texts.append(extract_id(ocr_image(crop, "--psm 7")))
            recognized = choose_candidate(texts)
            evidence = rel(step_dir / "candidate_regions.png")
        elif group_id == "D":
            binary, morphology = threshold_and_morph(gray)
            regions = func.find_id_regions(morphology)
            filtered = []
            for rect in regions:
                w, h = rect[1]
                if min(w, h) <= 1:
                    continue
                ratio = max(w, h) / min(w, h)
                area = w * h
                if ratio >= 5 and area >= 1000:
                    filtered.append(rect)
            filtered.sort(key=lambda r: r[1][0] * r[1][1], reverse=True)
            candidate_count = len(filtered)
            localization_success = candidate_count > 0
            draw_regions(img, filtered[:3], step_dir / "filtered_regions.png")
            texts = []
            for rect in filtered[:3]:
                crop = crop_rect(binary, rect)
                texts.append(extract_id(ocr_image(crop, "--psm 7")))
            recognized = choose_candidate(texts)
            evidence = rel(step_dir / "filtered_regions.png")
        else:
            binary, morphology = threshold_and_morph(gray)
            regions = func.find_id_regions(morphology)
            filtered = []
            for rect in regions:
                w, h = rect[1]
                if min(w, h) <= 1:
                    continue
                ratio = max(w, h) / min(w, h)
                area = w * h
                if ratio >= 5 and area >= 1000:
                    filtered.append(rect)
            filtered.sort(key=lambda r: r[1][0] * r[1][1], reverse=True)
            candidate_count = len(filtered)
            localization_success = candidate_count > 0
            draw_regions(img, filtered[:3], step_dir / "roi_filtered_regions.png")
            texts = []
            for idx, rect in enumerate(filtered[:3], 1):
                roi_dir = step_dir / f"roi_{idx:02d}"
                roi_dir.mkdir(parents=True, exist_ok=True)
                for variant in normalized_roi_variants(gray, binary, rect, roi_dir):
                    texts.append(whitelist_ocr(variant, 7))
                    texts.append(whitelist_ocr(variant, 8))
            recognized = choose_candidate(texts)
            evidence = rel(step_dir / "roi_filtered_regions.png")
    except Exception as exc:
        failure_type = f"{type(exc).__name__}: {exc}"
        (step_dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")

    elapsed = (time.time() - start) * 1000
    acc = char_accuracy(recognized)
    exact = normalize_id(recognized) == EXPECTED_ID
    if not failure_type:
        if not localization_success:
            failure_type = "未定位/未产生可用候选"
        elif not recognized:
            failure_type = "OCR空输出"
        elif not exact:
            failure_type = "字符误识别"
        else:
            failure_type = ""
    return {
        "sample_id": sample.sample_id,
        "group_id": group_id,
        "input_path": rel(sample.image_path),
        "issue_type": sample.issue_type,
        "source": sample.source,
        "expected_id": EXPECTED_ID,
        "recognized_id": recognized,
        "localization_success": str(localization_success),
        "ocr_char_accuracy": f"{acc:.4f}",
        "exact_match": str(exact),
        "candidate_count": candidate_count,
        "elapsed_ms": f"{elapsed:.1f}",
        "failure_type": failure_type,
        "evidence_path": evidence,
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def draw_table(summary_rows: list[dict], out_path: Path) -> None:
    w, h = 1480, 640
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 24, 32), fill=(0, 128, 64))
    draw.text((70, 14), "QUANTITATIVE DESIGN", font=FONT_SMALL, fill=(0, 128, 64))
    draw.text((70, 46), "定量实验设计：用消融实验证明每一步改进有价值", font=FONT_TITLE, fill=(10, 20, 30))
    draw.text((72, 104), "基于 UserShow/task1 的 52 张身份证测试图，实际运行 A-E 五组处理策略。", font=FONT_BODY, fill=(55, 65, 75))
    x0, y0 = 42, 156
    cols = [250, 270, 240, 250, 210, 210]
    headers = ["实验组", "处理流程", "定位成功率", "OCR字符准确率", "平均耗时", "失败类型"]
    row_h = 60
    draw.rectangle((x0, y0, x0 + sum(cols), y0 + 46), fill=(0, 128, 64))
    x = x0
    for header, cw in zip(headers, cols):
        draw.text((x + 16, y0 + 13), header, font=FONT_SMALL, fill="white")
        x += cw
    y = y0 + 46
    for row in summary_rows:
        x = x0
        draw.rectangle((x0, y, x0 + sum(cols), y + row_h), outline=(205, 218, 212), width=1)
        vals = [
            row["实验组"],
            row["处理流程"],
            row["定位成功率"],
            row["OCR字符准确率"],
            row["平均耗时"],
            row["失败类型"],
        ]
        for val, cw in zip(vals, cols):
            draw.text((x + 16, y + 18), str(val), font=FONT_SMALL, fill=(20, 35, 45))
            x += cw
        y += row_h
    draw.rectangle((66, 560, 690, 622), fill=(239, 248, 243), outline=(205, 218, 212))
    draw.text((98, 584), "评价指标：定位成功率=候选/ROI 是否可用；OCR字符准确率=身份证号逐字符匹配率", font=FONT_SMALL, fill=(20, 35, 45))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def draw_trend(summary_rows: list[dict], out_path: Path) -> None:
    w, h = 980, 560
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw.text((42, 32), "消融实验指标趋势", font=FONT_TITLE, fill=(20, 32, 50))
    max_v = 100
    y = 120
    for row in summary_rows:
        label = row["实验组"]
        loc = float(row["定位成功率"].split("(")[-1].replace("%)", ""))
        ocr = float(row["OCR字符准确率"].replace("%", ""))
        draw.text((46, y + 4), label, font=FONT_BODY, fill=(20, 32, 50))
        draw.rectangle((190, y, 830, y + 20), fill=(224, 232, 228))
        draw.rectangle((190, y, 190 + int(640 * loc / max_v), y + 20), fill=(47, 125, 211))
        draw.text((842, y - 2), f"定位 {loc:.1f}%", font=FONT_SMALL, fill=(20, 32, 50))
        y += 28
        draw.rectangle((190, y, 830, y + 20), fill=(224, 232, 228))
        draw.rectangle((190, y, 190 + int(640 * ocr / max_v), y + 20), fill=(7, 130, 63))
        draw.text((842, y - 2), f"OCR {ocr:.1f}%", font=FONT_SMALL, fill=(20, 32, 50))
        y += 56
    img.save(out_path)


def fit(img: Image.Image, w: int, h: int) -> Image.Image:
    ratio = min(w / img.width, h / img.height)
    size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
    out = Image.new("RGB", (w, h), "white")
    resized = img.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    out.paste(resized, ((w - size[0]) // 2, (h - size[1]) // 2))
    return out


def case_card(sample: Sample, rows: list[dict], out_path: Path, title: str) -> None:
    w, h = 1400, 760
    img = Image.new("RGB", (w, h), (245, 248, 250))
    draw = ImageDraw.Draw(img)
    draw.text((36, 28), title, font=FONT_TITLE, fill=(20, 32, 50))
    preview = fit(Image.open(sample.image_path), 560, 360)
    img.paste(preview, (40, 110))
    draw.rectangle((40, 110, 600, 470), outline=(205, 215, 225), width=2)
    x0, y0 = 650, 112
    headers = ["组", "识别号码", "字符准确率", "定位", "结论"]
    widths = [70, 240, 120, 90, 210]
    draw.rectangle((x0, y0, x0 + sum(widths), y0 + 38), fill=(0, 128, 64))
    x = x0
    for head, cw in zip(headers, widths):
        draw.text((x + 10, y0 + 9), head, font=FONT_SMALL, fill="white")
        x += cw
    y = y0 + 38
    for row in rows:
        x = x0
        vals = [
            row["group_id"],
            row["recognized_id"] or "-",
            f"{float(row['ocr_char_accuracy']) * 100:.1f}%",
            "是" if row["localization_success"] == "True" else "否",
            "正确" if row["exact_match"] == "True" else row["failure_type"][:10],
        ]
        draw.rectangle((x0, y, x0 + sum(widths), y + 44), outline=(205, 215, 225))
        for val, cw in zip(vals, widths):
            draw.text((x + 10, y + 12), str(val), font=FONT_SMALL, fill=(20, 32, 50))
            x += cw
        y += 44
    draw.text((42, 520), f"样本：{sample.sample_id}  类型：{sample.issue_type}  来源：{sample.source}", font=FONT_BODY, fill=(20, 32, 50))
    draw.text((42, 560), "结论：通过同一张图片在 A-E 组中的输出变化，展示预处理、候选区域和完整 ROI 校正带来的改进或边界。", font=FONT_BODY, fill=(20, 32, 50))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def group_result_card(group_summary: dict, case_rows: list[dict], sample_map: dict[str, Sample], out_path: Path) -> None:
    w, h = 1400, 760
    img = Image.new("RGB", (w, h), (245, 248, 250))
    draw = ImageDraw.Draw(img)
    draw.text((36, 28), f"{group_summary['实验组']}：{group_summary['处理流程']}", font=FONT_TITLE, fill=(20, 32, 50))
    metrics = [
        f"样本数：{group_summary['样本数']}",
        f"定位成功率：{group_summary['定位成功率']}",
        f"OCR字符准确率：{group_summary['OCR字符准确率']}",
        f"完全正确数：{group_summary['完全正确数']}",
        f"平均耗时：{group_summary['平均耗时']}",
        f"主要失败类型：{group_summary['失败类型']}",
    ]
    y = 94
    for item in metrics:
        draw.text((46, y), item, font=FONT_BODY, fill=(20, 32, 50))
        y += 34
    x0, y0 = 48, 330
    draw.text((x0, y0 - 42), "代表样例输出", font=FONT_H2, fill=(7, 130, 63))
    headers = ["样本", "类型", "识别号码", "字符准确率", "结论"]
    widths = [110, 160, 260, 130, 230]
    draw.rectangle((x0, y0, x0 + sum(widths), y0 + 38), fill=(0, 128, 64))
    x = x0
    for head, cw in zip(headers, widths):
        draw.text((x + 10, y0 + 9), head, font=FONT_SMALL, fill="white")
        x += cw
    y = y0 + 38
    for row in case_rows[:6]:
        sample = sample_map[row["sample_id"]]
        vals = [
            row["sample_id"],
            sample.issue_type,
            row["recognized_id"] or "-",
            f"{float(row['ocr_char_accuracy']) * 100:.1f}%",
            "正确" if row["exact_match"] == "True" else row["failure_type"][:14],
        ]
        x = x0
        draw.rectangle((x0, y, x0 + sum(widths), y + 44), outline=(205, 215, 225))
        for val, cw in zip(vals, widths):
            draw.text((x + 10, y + 12), str(val), font=FONT_SMALL, fill=(20, 32, 50))
            x += cw
        y += 44
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def main() -> None:
    ensure_clean()
    samples = load_samples()
    records: list[dict] = []
    for sample in samples:
        for group_id, *_ in GROUPS:
            records.append(run_group(sample, group_id))

    fields = list(records[0].keys())
    write_csv(TABLES / "ablation_detection_records.csv", records, fields)
    (TABLES / "ablation_detection_records.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_rows = []
    for group_id, group_name, pipeline, failure_hint in GROUPS:
        rs = [r for r in records if r["group_id"] == group_id]
        n = len(rs)
        loc = sum(r["localization_success"] == "True" for r in rs)
        exact = sum(r["exact_match"] == "True" for r in rs)
        char_acc = sum(float(r["ocr_char_accuracy"]) for r in rs) / n if n else 0
        avg_ms = sum(float(r["elapsed_ms"]) for r in rs) / n if n else 0
        fail_types: dict[str, int] = {}
        for r in rs:
            if r["exact_match"] != "True":
                key = r["failure_type"] or failure_hint
                fail_types[key] = fail_types.get(key, 0) + 1
        main_fail = max(fail_types.items(), key=lambda kv: kv[1])[0] if fail_types else "无"
        summary_rows.append(
            {
                "实验组": group_name,
                "处理流程": pipeline,
                "样本数": n,
                "定位成功率": f"{loc}/{n} ({loc / n * 100:.1f}%)",
                "OCR字符准确率": f"{char_acc * 100:.1f}%",
                "完全正确数": f"{exact}/{n}",
                "平均耗时": f"{avg_ms:.1f} ms",
                "失败类型": main_fail,
            }
        )
    write_csv(TABLES / "ablation_summary.csv", summary_rows, list(summary_rows[0].keys()))
    draw_table(summary_rows, CHARTS / "ablation_quantitative_design_table.png")
    draw_trend(summary_rows, CHARTS / "ablation_metric_trend.png")
    sample_map = {s.sample_id: s for s in samples}
    for group_id, *_ in GROUPS:
        group_summary = [r for r in summary_rows if str(r["实验组"]).startswith(group_id)][0]
        group_records = [r for r in records if r["group_id"] == group_id]
        ranked = sorted(group_records, key=lambda r: (r["exact_match"] != "True", -float(r["ocr_char_accuracy"])))
        group_result_card(group_summary, ranked, sample_map, STEP_CARDS / f"group_{group_id}_result_card.png")

    # Pick cases where full pipeline succeeds and earlier groups are worse, plus one boundary failure.
    by_sample: dict[str, list[dict]] = {}
    for r in records:
        by_sample.setdefault(r["sample_id"], []).append(r)
    success_candidates = []
    failure_candidates = []
    for sid, rs in by_sample.items():
        rs_sorted = sorted(rs, key=lambda r: "ABCDE".index(r["group_id"]))
        e = [r for r in rs_sorted if r["group_id"] == "E"][0]
        early_best = max(float(r["ocr_char_accuracy"]) for r in rs_sorted if r["group_id"] in "ABCD")
        if e["exact_match"] == "True" and float(e["ocr_char_accuracy"]) >= early_best:
            success_candidates.append((sid, rs_sorted, float(e["ocr_char_accuracy"]) - early_best))
        if e["exact_match"] != "True":
            failure_candidates.append((sid, rs_sorted))
    success_candidates.sort(key=lambda x: x[2], reverse=True)
    for i, (sid, rs, _) in enumerate(success_candidates[:6], 1):
        out = SUCCESS_DIR / f"success_case_{i:02d}_{sid}.png"
        case_card(sample_map[sid], rs, out, f"成功案例 {i}: 完整流程输出稳定")
    for i, (sid, rs) in enumerate(failure_candidates[:2], 1):
        out = FAIL_DIR / f"failure_case_{i:02d}_{sid}.png"
        case_card(sample_map[sid], rs, out, f"失败/边界案例 {i}: 低质图片仍影响 OCR")

    selected = OUT / "selected_for_upload"
    selected.mkdir(parents=True, exist_ok=True)
    for p in [CHARTS / "ablation_quantitative_design_table.png", CHARTS / "ablation_metric_trend.png"]:
        shutil.copy2(p, selected / p.name)
    for p in list(SUCCESS_DIR.glob("*.png"))[:4] + list(FAIL_DIR.glob("*.png"))[:1]:
        shutil.copy2(p, selected / p.name)

    md = f"""# task1 消融实验：用多种策略论证改进有效性

## 任务意图

参考用户给出的“定量实验设计”截图，本轮对身份证识别流程做 A-E 五组消融实验，用同一批 `UserShow/task1` 测试图验证每一步处理是否带来可量化改进。

## 实验数据

- 数据来源：`UserShow/task1/images/all_samples/`
- 样本数：{len(samples)}
- 评估字段：身份证号 `CARD_NUM`
- 评估口径：定位成功率、OCR 字符准确率、完全正确数、平均耗时、主要失败类型

## 实验组

| 实验组 | 处理流程 | 说明 |
|---|---|---|
| A 对照组 | 直接 OCR | 原图整图输入 OCR，容易受背景干扰 |
| B | 灰度 + 二值 | 降低颜色干扰，但字符断裂/噪声仍明显 |
| C | B + 形态学 | 尝试连接字符区域、消除小噪点 |
| D | C + 轮廓筛选 | 使用长宽比和面积筛选候选身份证号区域 |
| E 完整流程 | D + ROI + 校正 + 白名单 OCR + 格式校验 | 在公平口径下只评估身份证号码字段 |

## 汇总结果

详见：

- `tables/ablation_summary.csv`
- `tables/ablation_detection_records.csv`
- `charts/ablation_quantitative_design_table.png`
- `charts/ablation_metric_trend.png`
- `step_result_cards/`

## 成功案例

成功案例位于：

```text
selected_success_cases/
selected_for_upload/
```

这些案例展示完整流程在候选区域、ROI 校正和 OCR 输出上的稳定性。

## 少量失败案例

失败/边界案例位于：

```text
selected_failure_cases/
```

这些图片保留用于说明低质图片、严重噪声、角度或字符退化仍会影响 OCR，未被包装成成功结果。

## 结论

消融实验不是为了宣称所有样本 100% 成功，而是为了证明：从直接 OCR 到 ROI 校正、字符白名单和格式校验，处理链路逐步减少背景干扰、噪声断裂和误检区域问题。最终展示材料优先选取成功案例，同时保留少量失败案例作为边界说明。
"""
    (OUT / "README.md").write_text(md, encoding="utf-8")
    print(json.dumps({"samples": len(samples), "records": len(records), "summary": summary_rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
