import json

import requests

from core import vehicle_db


BASE_URL = "http://127.0.0.1:5000"


def session():
    s = requests.Session()
    s.trust_env = False
    return s


def main():
    vehicle_db.reset_database()
    s = session()
    try:
        init_resp = s.get(f"{BASE_URL}/api/vehicle/init")
        init_resp.raise_for_status()
        assert init_resp.json()["status"] == 1

        plate_resp = s.get(f"{BASE_URL}/api/vehicle/by-plate", params={"plate_no": "苏BD0011"})
        plate_resp.raise_for_status()
        plate_data = plate_resp.json()
        assert plate_data["status"] == 1
        assert plate_data["data"]["vehicle"]["plate_no"] == "苏BD0011"
        assert plate_data["data"]["owner"]["id_card"]

        owner_resp = s.get(f"{BASE_URL}/api/owner/by-id-card", params={"id_card": "44030119840217411X"})
        owner_resp.raise_for_status()
        owner_data = owner_resp.json()
        assert owner_data["status"] == 1
        assert owner_data["data"]["owner"]["name"] == "刘源"
        assert len(owner_data["data"]["vehicles"]) >= 1

        change_resp = s.post(f"{BASE_URL}/api/relationships/change-owner", json={
            "plate_no": "京A88888",
            "id_card": "44030119840217411X",
            "start_date": "2026-06-02",
            "event_location": "自动化测试登记点",
            "note": "接口测试动态变更",
        })
        change_resp.raise_for_status()
        change_data = change_resp.json()
        assert change_data["status"] == 1
        assert change_data["data"]["owner"]["id_card"] == "44030119840217411X"

        rel_resp = s.get(f"{BASE_URL}/api/relationships")
        rel_resp.raise_for_status()
        rel_data = rel_resp.json()
        assert rel_data["status"] == 1
        assert any(item["plate_no"] == "京A88888" for item in rel_data["data"])

        print(json.dumps({
            "vehicle_by_plate": plate_data["data"]["vehicle"]["plate_no"],
            "owner_by_id": owner_data["data"]["owner"]["name"],
            "changed_plate": change_data["data"]["plate_no"],
            "relationship_count_during_test": len(rel_data["data"]),
        }, ensure_ascii=False, indent=2))
    finally:
        vehicle_db.reset_database()


if __name__ == "__main__":
    main()
