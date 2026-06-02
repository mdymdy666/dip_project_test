import json
import os

import cv2
import requests

from core import vehicle_db


BASE_URL = "http://127.0.0.1:5000"
SMALL_IMAGE = os.path.join("uploads", "test_small.jpg")


def session():
    s = requests.Session()
    s.trust_env = False
    return s


def ensure_small_image():
    if os.path.exists(SMALL_IMAGE):
        return SMALL_IMAGE
    source = os.path.join("uploads", "default.jpg")
    image = cv2.imread(source)
    if image is None:
        raise FileNotFoundError(source)
    resized = cv2.resize(image, (240, 160))
    cv2.imwrite(SMALL_IMAGE, resized)
    return SMALL_IMAGE


def post_image(s, url, image_path):
    with open(image_path, "rb") as fp:
        resp = s.post(url, files={"file": (os.path.basename(image_path), fp, "image/jpeg")}, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != 1:
        raise AssertionError(f"{url} failed: {data}")
    return data


def main():
    vehicle_db.reset_database()
    s = session()
    image_path = ensure_small_image()
    result = {
        "pages": [],
        "image_processing_ids": [],
        "ocr": None,
        "plate": None,
        "database": None,
    }

    try:
        for path in [
            "/",
            "/upload/0",
            "/upload/13",
            "/upload/39",
            "/upload/50",
            "/upload/51",
            "/plate/recognize",
            "/vehicle/search",
            "/owner/search",
            "/relations",
        ]:
            resp = s.get(f"{BASE_URL}{path}", timeout=20)
            resp.raise_for_status()
            result["pages"].append(path)

        for process_id in list(range(0, 40)) + list(range(51, 60)):
            data = post_image(s, f"{BASE_URL}/upload/{process_id}", image_path)
            result["image_processing_ids"].append({
                "id": process_id,
                "draw_url": data.get("draw_url"),
            })

        id_image = os.path.join("uploads", "id01.jpg")
        ocr_data = post_image(s, f"{BASE_URL}/upload/50", id_image)
        if not ocr_data["ocr_text"].get("CARD_NUM"):
            raise AssertionError(f"OCR did not return CARD_NUM: {ocr_data['ocr_text']}")
        result["ocr"] = {
            "name": ocr_data["ocr_text"].get("CARD_NAME"),
            "id": ocr_data["ocr_text"].get("CARD_NUM"),
        }

        plate_image = os.path.join("uploads", "plate_test.png")
        with open(plate_image, "rb") as fp:
            plate_resp = s.post(
                f"{BASE_URL}/api/plate/recognize",
                files={"file": ("plate_test.png", fp, "image/png")},
                timeout=120,
            )
        plate_resp.raise_for_status()
        plate_data = plate_resp.json()
        if plate_data.get("status") != 1 or not plate_data.get("plates"):
            raise AssertionError(f"plate recognition failed: {plate_data}")
        result["plate"] = {
            "primary": plate_data["primary"]["plate_no"],
            "candidates": [item["plate_no"] for item in plate_data["plates"]],
        }

        init_data = s.get(f"{BASE_URL}/api/vehicle/init", timeout=20).json()
        by_plate = s.get(f"{BASE_URL}/api/vehicle/by-plate", params={"plate_no": "粤Z5A55港"}, timeout=20).json()
        by_owner = s.get(
            f"{BASE_URL}/api/owner/by-id-card",
            params={"id_card": "44030119840217411X"},
            timeout=20,
        ).json()
        change = s.post(
            f"{BASE_URL}/api/relationships/change-owner",
            json={
                "plate_no": "京A88888",
                "id_card": "44030119840217411X",
                "start_date": "2026-06-02",
                "event_location": "自动化综合测试登记点",
                "note": "综合测试动态变更",
            },
            timeout=20,
        ).json()
        relationships = s.get(f"{BASE_URL}/api/relationships", timeout=20).json()

        for name, data in [
            ("init", init_data),
            ("by_plate", by_plate),
            ("by_owner", by_owner),
            ("change", change),
            ("relationships", relationships),
        ]:
            if data.get("status") != 1:
                raise AssertionError(f"{name} API failed: {data}")

        result["database"] = {
            "summary": init_data.get("summary"),
            "plate_lookup_owner": by_plate["data"]["owner"]["name"],
            "owner_vehicle_count": len(by_owner["data"]["vehicles"]),
            "changed_owner": change["data"]["owner"]["name"],
            "relationship_count_during_test": len(relationships["data"]),
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        vehicle_db.reset_database()


if __name__ == "__main__":
    main()
