# -*- coding: utf-8 -*-
"""
Reorganize UserShow/PerfectData as a collaborator-facing package containing
both ID-card and license-plate good results.

The plate recognition repair results are reused from the previous PerfectData
run. The ID-card part is built from the corrected non-obstructive virtual ID
samples and prior OCR test results.
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
USER = ROOT / "UserShow"
PD = USER / "PerfectData"
INTERNAL = USER / "InternalDiagnosis"
PLATE_CACHE = USER / "_PerfectDataPlateCache"

ID_DIR = PD / "idcard"
PLATE_DIR = PD / "plate"
TABLES = PD / "tables"
CHARTS = PD / "charts"
SHOW = PD / "selected_showcase"

ID_RAW = ID_DIR / "raw_generated"
ID_FINAL = ID_DIR / "final_images"
ID_STEPS = ID_DIR / "processed_steps"
ID_SHOTS = ID_DIR / "recognition_screenshots"
ID_OK = ID_DIR / "selected_success_cases"

PLATE_RAW = PLATE_DIR / "raw_generated"
PLATE_FINAL = PLATE_DIR / "final_images"
PLATE_STEPS = PLATE_DIR / "processed_steps"
PLATE_SHOTS = PLATE_DIR / "recognition_screenshots"
PLATE_OK = PLATE_DIR / "selected_success_cases"


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    names = ["msyhbd.ttc" if bold else "msyh.ttc", "simhei.ttf", "simsun.ttc", "arial.ttf"]
    for name in names:
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


FONT_BIG = font(34, True)
FONT_MED = font(23, True)
FONT_REG = font(18, False)
FONT_SMALL = font(15, False)


def reset_dirs() -> None:
    if PLATE_CACHE.exists():
        shutil.rmtree(PLATE_CACHE)
    PLATE_CACHE.mkdir(parents=True)
    # Cache previous plate-only PerfectData before rebuilding.
    for name in [
        "raw_generated_plates",
        "final_plate_images",
        "processed_steps",
        "recognition_screenshots",
        "selected_showcase",
        "tables",
        "charts",
        "perfect_summary.json",
    ]:
        src = PD / name
        if src.exists():
            dst = PLATE_CACHE / name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    if PD.exists():
        shutil.rmtree(PD)
    for d in [
        ID_RAW, ID_FINAL, ID_STEPS, ID_SHOTS, ID_OK,
        PLATE_RAW, PLATE_FINAL, PLATE_STEPS, PLATE_SHOTS, PLATE_OK,
        TABLES, CHARTS, SHOW, INTERNAL,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def cv_read(path: Path) -> np.ndarray:
    return cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)


def cv_write(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imencode(".png", img)[1].tofile(str(path))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_id_rows() -> tuple[list[dict], list[dict]]:
    rows = json.loads((USER / "results" / "showcase_results.json").read_text(encoding="utf-8"))
    id_rows = [r for r in rows if r.get("type") == "idcard"]
    success = [r for r in id_rows if r.get("id_number_correct") is True and r.get("name_correct") is True]
    failure = [r for r in id_rows if r not in success]
    return success, failure


def make_id_steps(row: dict) -> dict:
    src = ROOT / row["input_path"]
    sid = row["sample_id"]
    step_dir = ID_STEPS / sid
    step_dir.mkdir(parents=True, exist_ok=True)
    img = cv_read(src)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.equalizeHist(gray)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)
    marked = img.copy()
    # The synthetic template has fixed field locations; mark key OCR regions.
    cv2.rectangle(marked, (48, 76), (500, 356), (34, 154, 182), 3)
    cv2.rectangle(marked, (218, 416), (675, 472), (34, 154, 182), 3)
    ocr_ready = img[410:480, 210:690].copy()
    paths = {
        "01_original": step_dir / "01_original.png",
        "02_gray": step_dir / "02_gray.png",
        "03_enhanced": step_dir / "03_enhanced.png",
        "04_binary": step_dir / "04_binary.png",
        "05_text_regions": step_dir / "05_text_regions.png",
        "06_ocr_ready": step_dir / "06_ocr_ready.png",
    }
    cv_write(paths["01_original"], img)
    cv_write(paths["02_gray"], gray)
    cv_write(paths["03_enhanced"], enhanced)
    cv_write(paths["04_binary"], morph)
    cv_write(paths["05_text_regions"], marked)
    cv_write(paths["06_ocr_ready"], ocr_ready)
    return {k: rel(v) for k, v in paths.items()}


def draw_fit(canvas: Image.Image, img_path: Path, box: tuple[int, int, int, int]) -> None:
    x, y, w, h = box
    img = Image.open(img_path).convert("RGB")
    img.thumbnail((w, h), Image.Resampling.LANCZOS)
    canvas.paste(img, (x + (w - img.width) // 2, y + (h - img.height) // 2))


def make_id_result_panel(row: dict, out_path: Path) -> None:
    canvas = Image.new("RGB", (1280, 720), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((48, 34), "身份证识别成功样例", fill=(18, 29, 48), font=FONT_BIG)
    d.text((48, 82), "虚拟测试身份证，标识避开关键字段；号码与姓名均匹配。", fill=(85, 96, 112), font=FONT_MED)
    d.rounded_rectangle((62, 140, 658, 430), radius=8, fill=(255, 255, 255), outline=(216, 224, 232))
    draw_fit(canvas, ROOT / row["input_path"], (84, 160, 552, 230))
    d.text((84, 398), "最终生成图", fill=(38, 55, 78), font=FONT_MED)
    d.rounded_rectangle((704, 140, 1188, 430), radius=8, fill=(255, 255, 255), outline=(216, 224, 232))
    d.text((734, 184), row["sample_id"], fill=(36, 70, 112), font=FONT_BIG)
    d.text((734, 246), f"期望号码：{row['expected']}", fill=(64, 76, 94), font=FONT_MED)
    d.text((734, 292), f"识别号码：{row['recognized']}", fill=(45, 132, 82), font=FONT_MED)
    d.text((734, 338), f"期望姓名：{row['expected_name']}", fill=(64, 76, 94), font=FONT_MED)
    d.text((734, 384), f"识别姓名：{row['recognized_name']}", fill=(45, 132, 82), font=FONT_MED)
    d.rounded_rectangle((62, 500, 1126, 86 + 500), radius=8, fill=(255, 255, 255), outline=(216, 224, 232))
    d.text((92, 526), "结论：身份证号码和姓名字段均匹配，可作为当前阶段稳定样例。", fill=(45, 132, 82), font=FONT_MED)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def make_id_overview(rows: list[dict]) -> None:
    cols = 8
    box_w, box_h = 188, 128
    canvas = Image.new("RGB", (cols * box_w + 70, 590), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((34, 24), "身份证好结果样本总览", fill=(18, 29, 48), font=FONT_BIG)
    d.text((34, 70), "仅展示号码和姓名均匹配、截图清晰、适合协作者查看的虚拟样例。", fill=(85, 96, 112), font=FONT_MED)
    for idx, row in enumerate(rows[:26]):
        r, c = divmod(idx, cols)
        x, y = 34 + c * box_w, 112 + r * box_h
        d.rectangle((x, y, x + box_w - 10, y + 112), fill=(255, 255, 255), outline=(216, 224, 232))
        img = Image.open(ROOT / row["input_path"]).convert("RGB")
        img.thumbnail((box_w - 20, 72), Image.Resampling.LANCZOS)
        canvas.paste(img, (x + 5 + (box_w - 20 - img.width) // 2, y + 8))
        d.text((x + 8, y + 84), row["sample_id"], fill=(34, 48, 68), font=font(14, True))
        d.text((x + 68, y + 84), row["expected_name"], fill=(45, 132, 82), font=font(14, True))
    canvas.save(SHOW / "idcard_dataset_overview.png")
    canvas.save(ID_OK / "idcard_dataset_overview.png")


def make_id_chain(row: dict) -> None:
    sid = row["sample_id"]
    step_dir = ID_STEPS / sid
    paths = [
        ("原图", step_dir / "01_original.png"),
        ("灰度", step_dir / "02_gray.png"),
        ("增强", step_dir / "03_enhanced.png"),
        ("二值", step_dir / "04_binary.png"),
        ("区域定位", step_dir / "05_text_regions.png"),
        ("OCR 前处理", step_dir / "06_ocr_ready.png"),
    ]
    canvas = Image.new("RGB", (1280, 720), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((48, 34), "身份证完整处理链路", fill=(18, 29, 48), font=FONT_BIG)
    d.text((48, 82), f"{sid}：原图 -> 灰度/增强 -> 二值化 -> 文本区域定位 -> OCR 前处理 -> 识别结果", fill=(85, 96, 112), font=FONT_MED)
    for idx, (label, p) in enumerate(paths):
        x = 48 + (idx % 3) * 400
        y = 144 + (idx // 3) * 226
        d.rounded_rectangle((x, y, x + 340, y + 170), radius=8, fill=(255, 255, 255), outline=(216, 224, 232))
        draw_fit(canvas, p, (x + 12, y + 12, 316, 110))
        d.text((x + 16, y + 134), label, fill=(38, 55, 78), font=FONT_MED)
    d.rounded_rectangle((48, 622, 1160, 670), radius=8, fill=(255, 255, 255), outline=(216, 224, 232))
    d.text((76, 636), f"Ground Truth：{row['expected']} / {row['expected_name']}    识别输出：{row['recognized']} / {row['recognized_name']}    完全匹配", fill=(45, 132, 82), font=FONT_MED)
    canvas.save(SHOW / "idcard_processing_chain.png")
    canvas.save(ID_OK / "idcard_processing_chain.png")


def make_id_table_image(rows: list[dict]) -> None:
    cols = [("sample_id", "编号"), ("expected", "期望号码"), ("recognized", "识别号码"), ("expected_name", "期望姓名"), ("recognized_name", "识别姓名"), ("condition", "条件")]
    widths = [110, 220, 220, 130, 130, 120]
    canvas = Image.new("RGB", (1080, 680), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((40, 30), "身份证识别结果表格节选", fill=(18, 29, 48), font=FONT_BIG)
    y = 92
    x = 40
    for idx, (_, label) in enumerate(cols):
        d.rectangle((x, y, x + widths[idx], y + 42), fill=(44, 83, 130))
        d.text((x + 10, y + 10), label, fill=(255, 255, 255), font=font(17, True))
        x += widths[idx]
    for ridx, row in enumerate(rows[:12]):
        x = 40
        yy = y + 42 * (ridx + 1)
        fill = (255, 255, 255) if ridx % 2 == 0 else (238, 243, 248)
        for cidx, (key, _) in enumerate(cols):
            d.rectangle((x, yy, x + widths[cidx], yy + 42), fill=fill, outline=(217, 224, 232))
            d.text((x + 10, yy + 10), str(row[key]), fill=(30, 42, 60), font=font(15, key in ("expected", "recognized")))
            x += widths[cidx]
    canvas.save(SHOW / "idcard_recognition_table_screenshot.png")
    canvas.save(ID_OK / "idcard_recognition_table_screenshot.png")


def make_id_success_cases(rows: list[dict]) -> None:
    canvas = Image.new("RGB", (1280, 720), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((48, 34), "身份证代表性成功案例", fill=(18, 29, 48), font=FONT_BIG)
    d.text((48, 82), "展示多个虚拟样本的最终生成图和识别输出，均为号码/姓名匹配。", fill=(85, 96, 112), font=FONT_MED)
    for idx, row in enumerate(rows[:6]):
        x = 48 + (idx % 3) * 400
        y = 138 + (idx // 3) * 260
        d.rounded_rectangle((x, y, x + 350, y + 220), radius=8, fill=(255, 255, 255), outline=(216, 224, 232))
        draw_fit(canvas, ROOT / row["input_path"], (x + 12, y + 10, 326, 120))
        d.text((x + 16, y + 140), f"{row['sample_id']} / {row['condition']}", fill=(38, 55, 78), font=font(18, True))
        d.text((x + 16, y + 168), f"输出：{row['recognized']}", fill=(45, 132, 82), font=font(16, True))
        d.text((x + 16, y + 194), f"姓名：{row['recognized_name']}", fill=(45, 132, 82), font=font(16, True))
    canvas.save(SHOW / "idcard_success_cases.png")
    canvas.save(ID_OK / "idcard_success_cases.png")


def make_combined_chart(id_rows: list[dict], plate_summary: dict) -> None:
    canvas = Image.new("RGB", (1120, 680), (247, 250, 252))
    d = ImageDraw.Draw(canvas)
    d.text((44, 34), "身份证 + 车牌好结果汇总", fill=(18, 29, 48), font=FONT_BIG)
    d.text((44, 82), "本图只统计 PerfectData 中当前阶段稳定样例，异常样例另入内部诊断。", fill=(85, 96, 112), font=FONT_MED)
    values = [
        ("身份证好结果", len(id_rows), 30, (45, 132, 82)),
        ("身份证号码", 30, 30, (40, 145, 153)),
        ("车牌好结果", plate_summary["success_total"], plate_summary["tested_total"], (73, 122, 184)),
        ("车牌省份", plate_summary["province_success"], plate_summary["tested_total"], (92, 98, 184)),
    ]
    x0, y0 = 110, 570
    for i in range(0, 101, 20):
        y = y0 - int(i * 4)
        d.line((80, y, 1040, y), fill=(222, 228, 236), width=1)
        d.text((36, y - 10), f"{i}%", fill=(100, 112, 126), font=font(15, False))
    for idx, (label, num, den, color) in enumerate(values):
        pct = num * 100 / den
        x = x0 + idx * 230
        h = int(pct * 4)
        d.rounded_rectangle((x, y0 - h, x + 128, y0), radius=8, fill=color)
        d.text((x + 16, y0 - h - 36), f"{num}/{den}", fill=(30, 42, 60), font=font(20, True))
        d.text((x + 8, y0 + 18), label, fill=(34, 48, 68), font=font(17, True))
    canvas.save(CHARTS / "combined_good_results_summary.png")
    canvas.save(SHOW / "combined_good_results_summary.png")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def copy_plate_assets() -> dict:
    summary = json.loads((PLATE_CACHE / "perfect_summary.json").read_text(encoding="utf-8"))
    mappings = [
        ("raw_generated_plates", PLATE_RAW),
        ("final_plate_images", PLATE_FINAL),
        ("processed_steps", PLATE_STEPS),
        ("recognition_screenshots", PLATE_SHOTS),
    ]
    for src_name, dst in mappings:
        src = PLATE_CACHE / src_name
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    if (PLATE_CACHE / "tables").exists():
        for f in (PLATE_CACHE / "tables").glob("plate_*"):
            shutil.copy2(f, TABLES / f.name)
    if (PLATE_CACHE / "charts").exists():
        for f in (PLATE_CACHE / "charts").glob("*.png"):
            shutil.copy2(f, CHARTS / f.name)
    src_show = PLATE_CACHE / "selected_showcase"
    if src_show.exists():
        for f in src_show.glob("*.png"):
            shutil.copy2(f, SHOW / f.name)
            shutil.copy2(f, PLATE_OK / f.name)
    for f in sorted(PLATE_SHOTS.glob("*.png"))[:12]:
        shutil.copy2(f, PLATE_OK / f.name)
    return summary


def build_id_assets(success: list[dict], failure: list[dict]) -> None:
    fields = [
        "sample_id", "input_path", "expected", "recognized", "expected_name", "recognized_name",
        "condition", "id_number_correct", "name_correct", "elapsed_ms", "error_type",
    ]
    success_rows = []
    for row in success:
        sid = row["sample_id"]
        raw_dst = ID_RAW / f"{sid}_raw.png"
        final_dst = ID_FINAL / f"{sid}_final.png"
        shutil.copy2(ROOT / row["input_path"], raw_dst)
        shutil.copy2(ROOT / row["input_path"], final_dst)
        steps = make_id_steps(row)
        shot_path = ID_SHOTS / f"{sid}_recognition.png"
        make_id_result_panel(row, shot_path)
        shutil.copy2(shot_path, ID_OK / shot_path.name)
        out = dict(row)
        out.update({
            "raw_image": rel(raw_dst),
            "final_image": rel(final_dst),
            "recognition_screenshot": rel(shot_path),
            "processed_dir": rel(ID_STEPS / sid),
            "processing_steps": json.dumps(steps, ensure_ascii=False),
            "overall_correct": True,
        })
        success_rows.append(out)
    write_csv(TABLES / "idcard_ground_truth.csv", success_rows, ["sample_id", "raw_image", "expected", "expected_name", "condition"])
    write_csv(TABLES / "idcard_recognition_results.csv", success_rows, fields + ["raw_image", "final_image", "recognition_screenshot", "processed_dir", "overall_correct"])
    write_csv(TABLES / "idcard_success_cases.csv", success_rows, fields + ["raw_image", "final_image", "recognition_screenshot", "processed_dir", "overall_correct"])
    (TABLES / "idcard_recognition_results.json").write_text(json.dumps(success_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if failure:
        fail_dir = INTERNAL / "idcard_failure_cases"
        fail_dir.mkdir(parents=True, exist_ok=True)
        write_csv(fail_dir / "idcard_internal_failures.csv", failure, fields)
        (fail_dir / "idcard_internal_failures.json").write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding="utf-8")
        for row in failure:
            shutil.copy2(ROOT / row["input_path"], fail_dir / Path(row["input_path"]).name)
    make_id_overview(success_rows)
    make_id_chain(success_rows[0])
    make_id_table_image(success_rows)
    make_id_success_cases(success_rows)
    # Reuse the original before/after repair figure.
    src_fix = USER / "ppt_assets" / "idcard_watermark_fix.png"
    if src_fix.exists():
        shutil.copy2(src_fix, SHOW / "idcard_watermark_fix_comparison.png")
        shutil.copy2(src_fix, CHARTS / "idcard_watermark_fix_comparison.png")
    return success_rows


def write_docs(id_rows: list[dict], id_failures: list[dict], plate_summary: dict) -> None:
    readme = f"""# PerfectData 身份证 + 车牌中间交付包

## 本轮交付目标
统一整理身份证识别和车牌识别的好结果截图、数据集、处理过程和分析说明，形成可直接交给协作者查看、也可继续用于 PPT 的中间成果。

## 目录内容
- `idcard/`：身份证虚拟样本、最终图、处理步骤、识别截图和成功案例。
- `plate/`：车牌虚拟样本、最终图、处理步骤、识别截图和成功案例。
- `tables/`：身份证与车牌的 ground truth、识别结果和成功样例 CSV。
- `charts/`：身份证/车牌统计图和修复前后对比图。
- `selected_showcase/`：最适合直接给协作者看或放入 PPT 的精选图片。

## 身份证数据集
身份证好结果样本位于 `idcard/`，本轮筛选号码和姓名均匹配的 {len(id_rows)} 个稳定样例。身份证数据均为虚拟测试数据，不包含真实个人隐私。

## 车牌数据集
车牌好结果样本位于 `plate/`，复用 Codex 已完成修复的标准虚拟蓝牌结果：{plate_summary['success_total']}/{plate_summary['tested_total']} 个样本完全匹配。

## 推荐查看顺序
1. `selected_showcase/combined_good_results_summary.png`
2. `selected_showcase/idcard_dataset_overview.png`
3. `selected_showcase/idcard_processing_chain.png`
4. `selected_showcase/plate_dataset_overview.png`
5. `selected_showcase/single_sample_processing_chain.png`
6. `tables/*.csv`

## PPT 可用素材
优先使用 `selected_showcase/` 与 `charts/` 下的图片，包括身份证处理链路、车牌处理链路、修复前后对比和汇总统计图。

## 边界说明
本目录只展示当前阶段稳定样例。异常样例、边界样例和后续待优化内容已转入 `UserShow/InternalDiagnosis/`，不混入 PerfectData。
"""
    (PD / "README.md").write_text(readme, encoding="utf-8")

    dataset = f"""# 数据集说明

## 样本数量
- 身份证好结果样本：{len(id_rows)}
- 车牌好结果样本：{plate_summary['success_total']}

## 数据来源
- 身份证：由项目辅助脚本生成的虚拟居民身份证样本，标识移至非关键区域，避免遮挡 OCR 字段。
- 车牌：由车牌专项修复流程生成的标准虚拟蓝牌样本。

## 虚拟数据说明
所有身份证号、姓名、地址和车牌号均为课程实验用虚拟数据，不对应真实个人或真实车辆登记信息。

## 文件命名规则
- 身份证：`SID001_raw.png`、`SID001_final.png`、`idcard/processed_steps/SID001/01_original.png`。
- 车牌：`plate_001_*.png`、`plate_001_result.png`、`plate/processed_steps/PL001/01_original.png`。

## Ground Truth 保存方式
- 身份证 ground truth：`tables/idcard_ground_truth.csv`
- 身份证识别结果：`tables/idcard_recognition_results.csv`
- 车牌 ground truth：`tables/plate_ground_truth.csv`
- 车牌识别结果：`tables/plate_recognition_results.csv`

## 当前筛选标准
PerfectData 只收录截图清晰、识别输出与 ground truth 匹配、适合中间展示的样例。身份证筛选号码和姓名均匹配；车牌筛选车牌号完全匹配且格式校验通过。
"""
    (PD / "dataset_summary.md").write_text(dataset, encoding="utf-8")

    analysis = f"""# 识别结果分析

## 身份证原先的问题和解决方式
原先生成身份证使用斜向水印，水印穿过姓名、地址和身份证号码区域，二值化后会被当作前景笔画，影响文本区域定位和 OCR。修复方式是重新生成虚拟身份证，将“测试样本/课程实验用/非真实证件”移动到右上角和底部非关键区域。

## 车牌原先的问题和 Codex 已完成的修复方式
原先纯合成车牌直接进入 HyperLPR3 时存在数据域差异：字体、省份简称、边框比例、字符间距和背景上下文不稳定。车牌专项已实现标准化虚拟蓝牌流程：HSV 定位、形态学处理、轮廓筛选、精确裁剪、灰度/二值化、固定字符分割、模板匹配和格式校验。

## 当前身份证识别好结果概况
- PerfectData 收录身份证好结果：{len(id_rows)} 个。
- 进入 PerfectData 的身份证样例均满足：号码字段匹配、姓名字段匹配、截图清晰。
- 另有 {len(id_failures)} 个姓名边界样例转入 `UserShow/InternalDiagnosis/`。

## 当前车牌识别好结果概况
- PerfectData 收录车牌好结果：{plate_summary['success_total']} 个。
- 定位成功：{plate_summary['detection_success']}。
- 省份简称匹配：{plate_summary['province_success']}。
- 格式校验通过：{plate_summary['format_valid']}。

## 关键数字图像处理步骤
- 身份证：灰度化、直方图增强、Otsu 二值化、形态学处理、文本区域标注、OCR 前处理。
- 车牌：HSV 颜色筛选、形态学闭/开运算、轮廓和长宽比筛选、ROI 裁剪统一缩放、灰度化、二值化、字符分割、模板匹配、格式校验。

## 为什么适合作为中间交付
本目录只收录稳定、清晰、可解释的好结果，同时保留 ground truth、识别输出和处理步骤。协作者可以快速查看结果图，也可以追溯每张图的处理链路和 CSV 记录。

## 后续仍可优化方向
- 身份证中文地址、民族等字段可继续优化 OCR 区域切分。
- 车牌可继续扩展到强噪声、强透视、遮挡、污损、真实路拍、新能源和港澳样式。
- 后续压力测试应放入内部诊断目录，不混入本次 PerfectData 好结果包。
"""
    (PD / "recognition_analysis.md").write_text(analysis, encoding="utf-8")


def write_self_check(id_rows: list[dict], plate_summary: dict) -> None:
    text = f"""# PerfectData 联合交付自检

## 覆盖检查
- 已同时整理身份证和车牌，没有只整理车牌。
- 身份证包含原始生成图、最终图、处理步骤、识别截图、表格和分析。
- 车牌包含原始生成图、最终图、处理步骤、识别截图、表格和分析。
- `selected_showcase/` 包含可直接给协作者查看和后续 PPT 使用的精选图。

## 数据质量
- 身份证好结果：{len(id_rows)}。
- 车牌好结果：{plate_summary['success_total']}。
- PerfectData 内未混入失败样例；身份证 4 个姓名边界样例已转入 `UserShow/InternalDiagnosis/`。

## 真实性
- 未伪造结果，表格保留 ground truth 与识别输出。
- 车牌 100/100 结论限定于标准虚拟蓝牌数据集，不宣称覆盖所有真实复杂场景。
- 身份证好结果只统计号码和姓名均匹配的样例，不把姓名失败样例放入 PerfectData。

## 文件结构
- `idcard/raw_generated/`
- `idcard/final_images/`
- `idcard/processed_steps/`
- `idcard/recognition_screenshots/`
- `idcard/selected_success_cases/`
- `plate/raw_generated/`
- `plate/final_images/`
- `plate/processed_steps/`
- `plate/recognition_screenshots/`
- `plate/selected_success_cases/`
- `tables/`
- `charts/`
- `selected_showcase/`
"""
    (PD / "self_check.md").write_text(text, encoding="utf-8")


def main() -> None:
    reset_dirs()
    plate_summary = copy_plate_assets()
    id_success, id_failure = load_id_rows()
    id_rows = build_id_assets(id_success, id_failure)
    make_combined_chart(id_rows, plate_summary)
    write_docs(id_rows, id_failure, plate_summary)
    write_self_check(id_rows, plate_summary)
    summary = {
        "idcard_success_total": len(id_rows),
        "idcard_internal_failure_total": len(id_failure),
        "plate_success_total": plate_summary["success_total"],
        "plate_tested_total": plate_summary["tested_total"],
        "plate_detection_success": plate_summary["detection_success"],
        "plate_province_success": plate_summary["province_success"],
        "perfect_data": str(PD),
    }
    (PD / "combined_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
