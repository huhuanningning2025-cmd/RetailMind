#!/usr/bin/env python3
"""Generate deterministic synthetic retail CSVs and the SQLite demo database."""

from __future__ import annotations

import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATABASE_PATH = DATA_DIR / "retailmind.db"
RANDOM_SEED = 20251010


PRODUCTS = [
    ("便携蓝牙音箱", "数码家电", "影音设备", 299.0, 178.0),
    ("降噪无线耳机", "数码家电", "影音设备", 699.0, 402.0),
    ("智能手环 Pro", "数码家电", "智能穿戴", 459.0, 265.0),
    ("65W 氮化镓充电器", "数码家电", "数码配件", 199.0, 91.0),
    ("机械键盘", "数码家电", "电脑外设", 389.0, 214.0),
    ("人体工学鼠标", "数码家电", "电脑外设", 249.0, 118.0),
    ("轻柔四件套", "家居生活", "床上用品", 429.0, 213.0),
    ("恒温保温杯", "家居生活", "餐厨用品", 159.0, 68.0),
    ("香薰加湿器", "家居生活", "生活电器", 239.0, 116.0),
    ("极简落地灯", "家居生活", "家居装饰", 329.0, 171.0),
    ("收纳套装", "家居生活", "收纳清洁", 129.0, 52.0),
    ("轻量通勤双肩包", "服饰鞋包", "箱包", 359.0, 176.0),
    ("基础款连帽卫衣", "服饰鞋包", "男装", 269.0, 112.0),
    ("羊毛混纺围巾", "服饰鞋包", "配饰", 219.0, 89.0),
    ("城市休闲鞋", "服饰鞋包", "鞋靴", 499.0, 231.0),
    ("冷萃咖啡组合", "食品饮料", "咖啡冲饮", 139.0, 61.0),
    ("每日坚果礼盒", "食品饮料", "休闲零食", 189.0, 97.0),
    ("高山乌龙茶", "食品饮料", "茶饮", 169.0, 72.0),
    ("低糖燕麦脆", "食品饮料", "健康食品", 79.0, 31.0),
    ("氨基酸洁面乳", "美妆个护", "面部护理", 119.0, 43.0),
    ("修护精华液", "美妆个护", "面部护理", 329.0, 116.0),
    ("木质香氛礼盒", "美妆个护", "香水香氛", 399.0, 171.0),
    ("便携电动牙刷", "美妆个护", "个人护理", 269.0, 127.0),
    ("轻量瑜伽垫", "运动户外", "瑜伽健身", 199.0, 83.0),
    ("速干运动 T 恤", "运动户外", "运动服饰", 159.0, 66.0),
    ("不锈钢运动水壶", "运动户外", "户外装备", 129.0, 49.0),
    ("城市骑行头盔", "运动户外", "骑行装备", 379.0, 201.0),
    ("可调节哑铃套装", "运动户外", "力量训练", 599.0, 323.0),
]

CITIES = [
    ("上海", "华东"), ("杭州", "华东"), ("南京", "华东"), ("苏州", "华东"),
    ("北京", "华北"), ("天津", "华北"), ("石家庄", "华北"),
    ("广州", "华南"), ("深圳", "华南"), ("厦门", "华南"),
    ("成都", "西南"), ("重庆", "西南"), ("昆明", "西南"),
    ("武汉", "华中"), ("长沙", "华中"), ("郑州", "华中"),
    ("西安", "西北"), ("兰州", "西北"),
    ("沈阳", "东北"), ("大连", "东北"),
]

SURNAMES = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦许何吕施张孔曹严华金魏陶姜谢邹喻柏水窦章云苏潘葛范彭郎鲁韦马苗凤花方俞任袁柳唐罗薛贺倪汤"
GIVEN_NAMES = ["晨", "宇", "子涵", "若曦", "嘉怡", "浩然", "思远", "雨桐", "俊杰", "欣怡", "文博", "佳宁", "明轩", "可心", "亦辰", "舒雅"]


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_rows() -> tuple[list[dict[str, object]], ...]:
    rng = random.Random(RANDOM_SEED)
    product_rows = [
        {
            "product_id": index,
            "product_name": name,
            "category": category,
            "subcategory": subcategory,
            "unit_price": price,
            "cost_price": cost,
        }
        for index, (name, category, subcategory, price, cost) in enumerate(PRODUCTS, 1)
    ]

    start = date(2023, 8, 1)
    customer_rows: list[dict[str, object]] = []
    for customer_id in range(1, 241):
        city, region = rng.choice(CITIES)
        customer_rows.append(
            {
                "customer_id": customer_id,
                "customer_name": rng.choice(SURNAMES) + rng.choice(GIVEN_NAMES),
                "city": city,
                "region": region,
                "segment": rng.choices(["新客", "成长客户", "高价值客户"], [36, 47, 17])[0],
                "signup_date": (start + timedelta(days=rng.randint(0, 500))).isoformat(),
            }
        )

    order_rows: list[dict[str, object]] = []
    item_rows: list[dict[str, object]] = []
    order_start = date(2024, 1, 1)
    item_id = 1
    product_weights = [18, 24, 14, 20, 15, 13, 10, 17, 12, 8, 15, 10, 12, 7, 14, 22, 21, 17, 15, 18, 16, 10, 14, 18, 13, 15, 8, 9]

    for order_id in range(1, 1801):
        day_offset = rng.randint(0, 730)
        order_date = order_start + timedelta(days=day_offset)
        # 让年末促销季的订单更集中，同时保持生成过程可复现。
        if order_date.month not in (6, 11, 12) and rng.random() < 0.18:
            order_date = order_date.replace(month=rng.choice([6, 11, 12]), day=rng.randint(1, 28))
        customer = rng.choices(customer_rows, weights=[1.7 if row["segment"] == "高价值客户" else 1.0 for row in customer_rows])[0]
        status = rng.choices(["已完成", "已取消", "已退款"], [89, 6, 5])[0]
        channel = rng.choices(["小程序", "电商平台", "线下门店", "直播间"], [34, 31, 23, 12])[0]
        payment = rng.choices(["微信支付", "支付宝", "银行卡"], [48, 37, 15])[0]
        order_rows.append(
            {
                "order_id": order_id,
                "customer_id": customer["customer_id"],
                "order_date": order_date.isoformat(),
                "status": status,
                "channel": channel,
                "payment_method": payment,
            }
        )

        product_ids = rng.choices(range(1, len(PRODUCTS) + 1), weights=product_weights, k=rng.randint(1, 4))
        for product_id in sorted(set(product_ids)):
            product = product_rows[product_id - 1]
            quantity = rng.choices([1, 2, 3, 4], [68, 23, 7, 2])[0]
            seasonal_discount = 0.05 if order_date.month in (6, 11, 12) else 0.0
            discount = min(0.2, rng.choices([0.0, 0.05, 0.1, 0.15], [48, 28, 18, 6])[0] + seasonal_discount)
            item_rows.append(
                {
                    "order_item_id": item_id,
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": product["unit_price"],
                    "discount_rate": round(discount, 2),
                }
            )
            item_id += 1
    return customer_rows, product_rows, order_rows, item_rows


def build_database(
    customer_rows: list[dict[str, object]],
    product_rows: list[dict[str, object]],
    order_rows: list[dict[str, object]],
    item_rows: list[dict[str, object]],
) -> None:
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            city TEXT NOT NULL,
            region TEXT NOT NULL,
            segment TEXT NOT NULL,
            signup_date TEXT NOT NULL
        );
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            cost_price REAL NOT NULL CHECK (cost_price >= 0)
        );
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
            order_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('已完成', '已取消', '已退款')),
            channel TEXT NOT NULL,
            payment_method TEXT NOT NULL
        );
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(order_id),
            product_id INTEGER NOT NULL REFERENCES products(product_id),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            discount_rate REAL NOT NULL CHECK (discount_rate BETWEEN 0 AND 1)
        );
        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_orders_date_status ON orders(order_date, status);
        CREATE INDEX idx_items_order ON order_items(order_id);
        CREATE INDEX idx_items_product ON order_items(product_id);
        CREATE INDEX idx_products_category ON products(category);
        """
    )
    connection.executemany(
        "INSERT INTO customers VALUES (:customer_id, :customer_name, :city, :region, :segment, :signup_date)",
        customer_rows,
    )
    connection.executemany(
        "INSERT INTO products VALUES (:product_id, :product_name, :category, :subcategory, :unit_price, :cost_price)",
        product_rows,
    )
    connection.executemany(
        "INSERT INTO orders VALUES (:order_id, :customer_id, :order_date, :status, :channel, :payment_method)",
        order_rows,
    )
    connection.executemany(
        "INSERT INTO order_items VALUES (:order_item_id, :order_id, :product_id, :quantity, :unit_price, :discount_rate)",
        item_rows,
    )
    connection.commit()
    connection.execute("ANALYZE")
    connection.commit()
    connection.close()


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    customer_rows, product_rows, order_rows, item_rows = build_rows()
    _write_csv(DATA_DIR / "customers.csv", list(customer_rows[0]), customer_rows)
    _write_csv(DATA_DIR / "products.csv", list(product_rows[0]), product_rows)
    _write_csv(DATA_DIR / "orders.csv", list(order_rows[0]), order_rows)
    _write_csv(DATA_DIR / "order_items.csv", list(item_rows[0]), item_rows)
    build_database(customer_rows, product_rows, order_rows, item_rows)
    print(
        f"Generated {DATABASE_PATH}: {len(customer_rows)} customers, "
        f"{len(product_rows)} products, {len(order_rows)} orders, {len(item_rows)} items."
    )


if __name__ == "__main__":
    main()

