import os
import sqlite3
from datetime import date


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "vehicle_owner.db")


OWNER_SEEDS = [
    ("44030119840217411X", "刘源", "男", "汉", "1984-02-17", "广东省深圳市福田区益村115栋21A", "13800010001"),
    ("110101199003077512", "周明", "男", "汉", "1990-03-07", "北京市东城区东华门街道", "13800010002"),
    ("320102198806152024", "陈芸", "女", "汉", "1988-06-15", "江苏省南京市玄武区珠江路", "13800010003"),
    ("440106199512082639", "林晓", "女", "汉", "1995-12-08", "广东省广州市天河区体育西路", "13800010004"),
    ("110103198211290041", "李彤", "女", "汉", "1982-11-29", "北京市西城区洪福胡同5号西门201号", "13800010005"),
    ("43062419900818361X", "钟岸", "男", "汉", "1990-08-18", "湖南省岳阳市湘阴县文星街道", "13800010006"),
    ("31010119870722321X", "赵然", "男", "汉", "1987-07-22", "上海市黄浦区人民大道188号", "13800010007"),
    ("510104199110304526", "黄静", "女", "汉", "1991-10-30", "四川省成都市锦江区春熙路", "13800010008"),
    ("330106198905064218", "许晨", "男", "汉", "1989-05-06", "浙江省杭州市西湖区文三路", "13800010009"),
    ("440305199902141234", "邓琪", "女", "汉", "1999-02-14", "广东省深圳市南山区科技园", "13800010010"),
    ("120101197912120030", "马骏", "男", "回", "1979-12-12", "天津市和平区南京路", "13800010011"),
    ("500103198303184512", "唐悦", "女", "土家", "1983-03-18", "重庆市渝中区解放碑", "13800010012"),
]


VEHICLE_SEEDS = [
    ("苏BD0011", "比亚迪", "秦 PLUS DM-i", "2023-04-18", "蓝色", "新能源轿车", "江苏省南京市玄武区", "在用"),
    ("粤Z5A55港", "丰田", "埃尔法", "2021-09-12", "黑色", "商务车", "广东省深圳市福田口岸", "在用"),
    ("粤B12345", "特斯拉", "Model 3", "2022-11-03", "白色", "新能源轿车", "广东省深圳市南山区", "在用"),
    ("京A88888", "奥迪", "A6L", "2020-05-20", "灰色", "轿车", "北京市朝阳区", "在用"),
    ("沪C77889", "大众", "帕萨特", "2019-08-28", "黑色", "轿车", "上海市浦东新区", "在用"),
    ("川A6T889", "宝马", "X3", "2021-01-10", "白色", "SUV", "四川省成都市锦江区", "在用"),
    ("浙A1Q8K6", "蔚来", "ES6", "2024-03-02", "灰色", "新能源SUV", "浙江省杭州市西湖区", "在用"),
    ("粤B9K321", "小鹏", "P7", "2022-07-19", "银色", "新能源轿车", "广东省深圳市南山区", "在用"),
    ("津B22880", "吉利", "星瑞", "2020-10-11", "蓝色", "轿车", "天津市和平区", "在用"),
    ("渝A7M316", "长安", "CS75 PLUS", "2021-06-22", "红色", "SUV", "重庆市渝中区", "在用"),
    ("苏E0P512", "理想", "L6", "2025-01-08", "绿色", "新能源SUV", "江苏省苏州市工业园区", "在用"),
    ("京N34567", "奔驰", "GLC", "2018-12-05", "黑色", "SUV", "北京市海淀区", "维修"),
    ("粤A6D789", "本田", "雅阁", "2017-04-14", "白色", "轿车", "广东省广州市天河区", "在用"),
    ("沪A3R215", "宝马", "5系", "2019-11-20", "蓝色", "轿车", "上海市黄浦区", "停驶"),
]


HISTORY_SEEDS = [
    ("苏BD0011", "320102198806152024", "2023-05-01", "2025-01-15", "江苏省南京市玄武区", "新车登记"),
    ("苏BD0011", "44030119840217411X", "2025-01-16", None, "广东省深圳市福田区", "二手车过户"),
    ("粤Z5A55港", "440106199512082639", "2021-10-01", "2024-03-18", "香港特别行政区", "公司车辆登记"),
    ("粤Z5A55港", "44030119840217411X", "2024-03-19", None, "广东省深圳市福田口岸", "跨境车辆转入"),
    ("粤B12345", "44030119840217411X", "2022-12-01", None, "广东省深圳市南山区", "家庭自用车"),
    ("京A88888", "110101199003077512", "2020-06-01", "2023-07-31", "北京市朝阳区", "个人名下车辆"),
    ("京A88888", "110103198211290041", "2023-08-01", None, "北京市西城区", "亲属间转让"),
    ("沪C77889", "31010119870722321X", "2019-09-15", None, "上海市浦东新区", "通勤车辆"),
    ("川A6T889", "510104199110304526", "2021-02-08", None, "四川省成都市锦江区", "家庭SUV"),
    ("浙A1Q8K6", "330106198905064218", "2024-03-20", None, "浙江省杭州市西湖区", "新能源置换"),
    ("粤B9K321", "440305199902141234", "2022-08-03", None, "广东省深圳市南山区", "个人首购车辆"),
    ("津B22880", "120101197912120030", "2020-11-01", None, "天津市和平区", "单位通勤"),
    ("渝A7M316", "500103198303184512", "2021-07-06", None, "重庆市渝中区", "家庭车辆"),
    ("苏E0P512", "320102198806152024", "2025-02-01", None, "江苏省苏州市工业园区", "增购新能源"),
    ("京N34567", "110101199003077512", "2019-01-01", "2022-09-10", "北京市海淀区", "初次登记"),
    ("京N34567", "43062419900818361X", "2022-09-11", None, "北京市海淀区", "异地转入"),
    ("粤A6D789", "440106199512082639", "2017-05-02", "2021-03-11", "广东省广州市天河区", "旧车登记"),
    ("粤A6D789", "43062419900818361X", "2021-03-12", None, "湖南省岳阳市湘阴县", "二手车交易"),
    ("沪A3R215", "31010119870722321X", "2019-12-10", "2024-04-20", "上海市黄浦区", "个人登记"),
    ("沪A3R215", "440305199902141234", "2024-04-21", None, "广东省深圳市南山区", "跨省迁入"),
]


def _connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row):
    return dict(row) if row is not None else None


def _rows_to_dicts(rows):
    return [dict(row) for row in rows]


def _create_schema(cur):
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS owners (
            id_card TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT,
            ethnicity TEXT,
            birthday TEXT,
            address TEXT,
            phone TEXT
        );

        CREATE TABLE IF NOT EXISTS vehicles (
            plate_no TEXT PRIMARY KEY,
            brand TEXT NOT NULL,
            model TEXT,
            production_date TEXT,
            color TEXT,
            vehicle_type TEXT,
            current_location TEXT,
            status TEXT
        );

        CREATE TABLE IF NOT EXISTS ownership_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_no TEXT NOT NULL,
            id_card TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            event_location TEXT,
            note TEXT,
            FOREIGN KEY (plate_no) REFERENCES vehicles(plate_no),
            FOREIGN KEY (id_card) REFERENCES owners(id_card)
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_ownership_history_seed
        ON ownership_history (plate_no, id_card, start_date);
        """
    )


def _seed_database(cur):
    cur.executemany(
        """
        INSERT OR IGNORE INTO owners
        (id_card, name, gender, ethnicity, birthday, address, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        OWNER_SEEDS,
    )
    cur.executemany(
        """
        INSERT OR IGNORE INTO vehicles
        (plate_no, brand, model, production_date, color, vehicle_type, current_location, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        VEHICLE_SEEDS,
    )
    cur.executemany(
        """
        INSERT OR IGNORE INTO ownership_history
        (plate_no, id_card, start_date, end_date, event_location, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        HISTORY_SEEDS,
    )


def init_database():
    conn = _connect()
    cur = conn.cursor()
    _create_schema(cur)
    _seed_database(cur)
    conn.commit()
    conn.close()
    return DB_PATH


def reset_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    return init_database()


def get_vehicle(plate_no):
    init_database()
    conn = _connect()
    row = conn.execute("SELECT * FROM vehicles WHERE plate_no = ?", (plate_no,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_owner(id_card):
    init_database()
    conn = _connect()
    row = conn.execute("SELECT * FROM owners WHERE id_card = ?", (id_card,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_history_by_plate(plate_no):
    init_database()
    conn = _connect()
    rows = conn.execute(
        """
        SELECT h.*, o.name, o.gender, o.phone
        FROM ownership_history h
        JOIN owners o ON h.id_card = o.id_card
        WHERE h.plate_no = ?
        ORDER BY h.start_date DESC, h.id DESC
        """,
        (plate_no,),
    ).fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_vehicles_by_owner(id_card):
    init_database()
    conn = _connect()
    rows = conn.execute(
        """
        SELECT v.*, h.start_date, h.end_date, h.event_location, h.note
        FROM ownership_history h
        JOIN vehicles v ON h.plate_no = v.plate_no
        WHERE h.id_card = ?
        ORDER BY COALESCE(h.end_date, '9999-12-31') DESC, h.start_date DESC
        """,
        (id_card,),
    ).fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_current_owner(plate_no):
    init_database()
    conn = _connect()
    row = conn.execute(
        """
        SELECT o.*, h.start_date, h.event_location, h.note
        FROM ownership_history h
        JOIN owners o ON h.id_card = o.id_card
        WHERE h.plate_no = ? AND h.end_date IS NULL
        ORDER BY h.start_date DESC, h.id DESC
        LIMIT 1
        """,
        (plate_no,),
    ).fetchone()
    conn.close()
    return _row_to_dict(row)


def lookup_vehicle_with_owner(plate_no):
    return {
        "plate_no": plate_no,
        "vehicle": get_vehicle(plate_no),
        "owner": get_current_owner(plate_no),
        "history": get_history_by_plate(plate_no),
    }


def lookup_owner_with_vehicles(id_card):
    return {
        "id_card": id_card,
        "owner": get_owner(id_card),
        "vehicles": get_vehicles_by_owner(id_card),
    }


def list_relationships():
    init_database()
    conn = _connect()
    rows = conn.execute(
        """
        SELECT h.*, o.name, v.brand, v.model, v.current_location
        FROM ownership_history h
        JOIN owners o ON h.id_card = o.id_card
        JOIN vehicles v ON h.plate_no = v.plate_no
        ORDER BY COALESCE(h.end_date, '9999-12-31') DESC, h.start_date DESC, h.id DESC
        """
    ).fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def database_summary():
    init_database()
    conn = _connect()
    counts = {
        "owners": conn.execute("SELECT COUNT(*) FROM owners").fetchone()[0],
        "vehicles": conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0],
        "ownership_history": conn.execute("SELECT COUNT(*) FROM ownership_history").fetchone()[0],
        "current_relationships": conn.execute(
            "SELECT COUNT(*) FROM ownership_history WHERE end_date IS NULL"
        ).fetchone()[0],
    }
    conn.close()
    return counts


def change_owner(plate_no, id_card, start_date=None, event_location="", note="动态变更"):
    init_database()
    if not get_vehicle(plate_no):
        raise ValueError("车辆不存在")
    if not get_owner(id_card):
        raise ValueError("车主不存在")
    start_date = start_date or date.today().isoformat()
    current_owner = get_current_owner(plate_no)
    if current_owner and current_owner["id_card"] == id_card:
        raise ValueError("当前车主已经是该身份证")

    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE ownership_history SET end_date = ? WHERE plate_no = ? AND end_date IS NULL",
        (start_date, plate_no),
    )
    cur.execute(
        """
        INSERT INTO ownership_history
        (plate_no, id_card, start_date, end_date, event_location, note)
        VALUES (?, ?, ?, NULL, ?, ?)
        """,
        (plate_no, id_card, start_date, event_location, note),
    )
    conn.commit()
    conn.close()
    return lookup_vehicle_with_owner(plate_no)
