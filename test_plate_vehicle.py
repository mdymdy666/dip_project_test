import json
import os

from core import plate_operation, vehicle_db


def main():
    db_path = vehicle_db.init_database()
    image_path = os.path.join("uploads", "plate_test.png")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"missing plate test image: {image_path}")

    result = plate_operation.recognize(image_path)
    if not result["plates"]:
        raise AssertionError("HyperLPR3 did not detect any license plate")

    primary = result["primary"]
    lookup = vehicle_db.lookup_vehicle_with_owner(primary["plate_no"])
    if not lookup["vehicle"]:
        raise AssertionError(f"recognized plate is not in vehicle database: {primary['plate_no']}")
    if not lookup["owner"]:
        raise AssertionError(f"recognized plate has no active owner: {primary['plate_no']}")

    print(json.dumps({
        "db_path": db_path,
        "primary_plate": primary["plate_no"],
        "confidence": primary["confidence"],
        "vehicle": lookup["vehicle"],
        "owner": lookup["owner"],
        "history_count": len(lookup["history"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
