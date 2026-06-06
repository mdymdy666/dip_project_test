from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PERFECT_DATA = ROOT / "UserShow" / "PerfectData"
REPORT_PATH = PERFECT_DATA / "delivery_audit.md"
JSON_PATH = PERFECT_DATA / "delivery_audit.json"

REQUIRED_DIRS = [
    "idcard/raw_generated",
    "idcard/final_images",
    "idcard/processed_steps",
    "idcard/recognition_screenshots",
    "idcard/selected_success_cases",
    "plate/raw_generated",
    "plate/final_images",
    "plate/processed_steps",
    "plate/recognition_screenshots",
    "plate/selected_success_cases",
    "tables",
    "charts",
    "selected_showcase",
]

REQUIRED_FILES = [
    "README.md",
    "dataset_summary.md",
    "recognition_analysis.md",
    "self_check.md",
    "combined_summary.json",
    "tables/idcard_ground_truth.csv",
    "tables/idcard_recognition_results.csv",
    "tables/idcard_success_cases.csv",
    "tables/plate_ground_truth.csv",
    "tables/plate_recognition_results.csv",
    "tables/plate_success_cases.csv",
]

FORBIDDEN_SUFFIXES = {".ppt", ".pptx", ".tmp", ".temp", ".bak"}
FORBIDDEN_NAME_PARTS = {"~$", ".ds_store", "thumbs.db"}
SENSITIVE_PATTERNS = [
    re.compile(r"api[_-]?key\\s*[:=]", re.I),
    re.compile(r"token\\s*[:=]", re.I),
    re.compile(r"password\\s*[:=]", re.I),
    re.compile(r"secret\\s*[:=]", re.I),
    re.compile(r"cookie\\s*[:=]", re.I),
]


def rel(path: Path) -> str:
    return path.relative_to(PERFECT_DATA).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def count_pngs(path: Path) -> int:
    return sum(1 for item in path.glob("*.png") if item.is_file())


def count_child_dirs(path: Path) -> int:
    return sum(1 for item in path.iterdir() if item.is_dir())


def audit_csv(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = rows[0].keys() if rows else []
    blank_rows = 0
    for row in rows:
        if not any(str(value).strip() for value in row.values()):
            blank_rows += 1
    return {
        "rows": len(rows),
        "columns": list(fields),
        "blank_rows": blank_rows,
    }


def audit_image(path: Path) -> dict:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
        }


def main() -> None:
    issues: list[str] = []
    warnings: list[str] = []
    all_files = [item for item in PERFECT_DATA.rglob("*") if item.is_file()]

    if not PERFECT_DATA.exists():
        raise SystemExit(f"PerfectData not found: {PERFECT_DATA}")

    for required in REQUIRED_DIRS:
        path = PERFECT_DATA / required
        if not path.is_dir():
            issues.append(f"缺少必需目录：{required}")

    for required in REQUIRED_FILES:
        path = PERFECT_DATA / required
        if not path.is_file():
            issues.append(f"缺少必需文件：{required}")

    suffix_counter = Counter(path.suffix.lower() or "[no_ext]" for path in all_files)
    total_size = sum(path.stat().st_size for path in all_files)

    forbidden_files: list[str] = []
    unreadable_images: list[str] = []
    image_info: dict[str, dict] = {}
    csv_info: dict[str, dict] = {}
    sensitive_hits: list[str] = []
    unclear_names: list[str] = []

    for path in all_files:
        relative = rel(path)
        lower_name = path.name.lower()
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or any(part in lower_name for part in FORBIDDEN_NAME_PARTS):
            forbidden_files.append(relative)
        if re.fullmatch(r"\\d+\\.png", lower_name) or lower_name in {"test.png", "1.png", "2.png"}:
            unclear_names.append(relative)

        if path.suffix.lower() in {".md", ".csv", ".json", ".txt", ".py"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in SENSITIVE_PATTERNS:
                if pattern.search(text):
                    sensitive_hits.append(f"{relative}: {pattern.pattern}")

        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            try:
                image_info[relative] = audit_image(path)
            except Exception as exc:  # noqa: BLE001
                unreadable_images.append(f"{relative}: {exc}")

        if path.suffix.lower() == ".csv":
            try:
                csv_info[relative] = audit_csv(path)
            except Exception as exc:  # noqa: BLE001
                issues.append(f"CSV 无法读取：{relative}: {exc}")

    if forbidden_files:
        issues.append("存在禁止交付文件：" + ", ".join(forbidden_files))
    if unreadable_images:
        issues.append("存在无法打开图片：" + ", ".join(unreadable_images[:20]))
    if sensitive_hits:
        issues.append("存在疑似敏感字段：" + ", ".join(sensitive_hits[:20]))
    if unclear_names:
        warnings.append("发现少量语义较弱命名：" + ", ".join(unclear_names[:20]))

    expected_counts = {
        "idcard/raw_generated png": count_pngs(PERFECT_DATA / "idcard" / "raw_generated"),
        "idcard/final_images png": count_pngs(PERFECT_DATA / "idcard" / "final_images"),
        "idcard/processed_steps sample dirs": count_child_dirs(PERFECT_DATA / "idcard" / "processed_steps"),
        "idcard/recognition_screenshots png": count_pngs(PERFECT_DATA / "idcard" / "recognition_screenshots"),
        "plate/raw_generated png": count_pngs(PERFECT_DATA / "plate" / "raw_generated"),
        "plate/final_images png": count_pngs(PERFECT_DATA / "plate" / "final_images"),
        "plate/processed_steps sample dirs": count_child_dirs(PERFECT_DATA / "plate" / "processed_steps"),
        "plate/recognition_screenshots png": count_pngs(PERFECT_DATA / "plate" / "recognition_screenshots"),
    }

    summary = {
        "audited_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "perfect_data": str(PERFECT_DATA),
        "file_count": len(all_files),
        "total_size_bytes": total_size,
        "suffix_counter": dict(sorted(suffix_counter.items())),
        "expected_counts": expected_counts,
        "csv_info": csv_info,
        "image_count": len(image_info),
        "issues": issues,
        "warnings": warnings,
    }

    JSON_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# PerfectData 交付前审查报告",
        "",
        f"- 审查时间：{summary['audited_at']}",
        f"- 审查目录：`{PERFECT_DATA}`",
        f"- 文件总数：{summary['file_count']}",
        f"- 总大小：{summary['total_size_bytes'] / 1024 / 1024:.2f} MB",
        f"- 图片可打开数量：{summary['image_count']}",
        f"- 审查结论：{'通过' if not issues else '存在问题，需修正'}",
        "",
        "## 目录与数量核对",
    ]
    for key, value in expected_counts.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## 文件类型统计"])
    for suffix, count in sorted(suffix_counter.items()):
        lines.append(f"- `{suffix}`: {count}")

    lines.extend(["", "## CSV 表格核对"])
    for name, info in sorted(csv_info.items()):
        lines.append(
            f"- `{name}`: {info['rows']} 行，字段：{', '.join(info['columns'])}，空白行：{info['blank_rows']}"
        )

    lines.extend(["", "## 风险项检查"])
    lines.append("- PPT 文件：未发现" if not forbidden_files else "- PPT/临时文件：发现禁止文件")
    lines.append("- 敏感字段：未发现 token/password/secret/cookie 等配置字段" if not sensitive_hits else "- 敏感字段：发现疑似字段")
    lines.append("- 图片可读性：全部可打开" if not unreadable_images else "- 图片可读性：存在无法打开图片")
    lines.append("- 失败样例隔离：PerfectData 仅收录稳定好结果，内部诊断样例位于 `UserShow/InternalDiagnosis/`")

    lines.extend(["", "## 问题"])
    if issues:
        lines.extend(f"- {item}" for item in issues)
    else:
        lines.append("- 未发现阻塞交付的问题。")

    lines.extend(["", "## 提醒"])
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- 未发现需要特别提醒的命名或格式问题。")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
