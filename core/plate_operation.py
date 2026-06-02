import os
import re

import cv2
import numpy as np

from core import vehicle_db


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PARENT = os.path.join(BASE_DIR, "models")
MODEL_FOLDER = os.path.join(MODEL_PARENT, ".hyperlpr3")

os.environ["HOMEPATH"] = MODEL_PARENT

_catcher = None


def _get_catcher():
    global _catcher
    if _catcher is None:
        from hyperlpr3 import LicensePlateCatcher
        _catcher = LicensePlateCatcher(folder=MODEL_FOLDER)
    return _catcher


def _normalize_plate(text):
    return re.sub(r"\s+", "", text or "").upper()


def _to_python_number(value):
    if isinstance(value, np.generic):
        return value.item()
    return value


def _format_result(raw_result):
    plate_no, confidence, plate_type, box = raw_result
    plate_no = _normalize_plate(plate_no)
    return {
        "plate_no": plate_no,
        "confidence": round(float(_to_python_number(confidence)), 4),
        "plate_type": int(_to_python_number(plate_type)),
        "box": [int(x) for x in box],
        "lookup": vehicle_db.lookup_vehicle_with_owner(plate_no),
    }


def _draw_results(image, results):
    output = image.copy()
    for item in results:
        x1, y1, x2, y2 = item["box"]
        cv2.rectangle(output, (x1, y1), (x2, y2), (35, 154, 182), 3)
        label = f"{item['plate_no']} {item['confidence']:.2f}"
        safe_label = label.encode("ascii", "replace").decode("ascii")
        cv2.putText(output, safe_label, (x1, max(24, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (196, 73, 57), 2)
    return output


def recognize(path):
    image = cv2.imread(path)
    if image is None:
        raise ValueError("图片读取失败")

    catcher = _get_catcher()
    raw_results = catcher(image)
    results = [_format_result(item) for item in raw_results]
    results.sort(key=lambda item: item["confidence"], reverse=True)

    file_name = os.path.splitext(os.path.basename(path))[0]
    output_name = f"plate_{file_name}.png"
    output_path = os.path.join(BASE_DIR, "tmp", "draw", output_name)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imencode(".png", _draw_results(image, results))[1].tofile(output_path)

    return {
        "plates": results,
        "primary": results[0] if results else None,
        "draw_name": output_name,
    }
