from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoQuery:
    question: str
    title: str
    sql: str
    chart_hint: str
    description: str


DEMO_QUERIES: tuple[DemoQuery, ...] = (
    DemoQuery(
        question="每月销售额趋势如何？",
        title="月度销售趋势",
        chart_hint="line",
        description="按月观察已完成订单的销售额、订单量与客单价。",
        sql="""
            SELECT
                strftime('%Y-%m', o.order_date) AS 月份,
                ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate)), 2) AS 销售额,
                COUNT(DISTINCT o.order_id) AS 订单量,
                ROUND(
                    SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate))
                    / COUNT(DISTINCT o.order_id), 2
                ) AS 客单价
            FROM orders AS o
            JOIN order_items AS oi ON oi.order_id = o.order_id
            WHERE o.status = '已完成'
            GROUP BY strftime('%Y-%m', o.order_date)
            ORDER BY 月份
        """,
    ),
    DemoQuery(
        question="销售额最高的 10 个商品是什么？",
        title="商品销售额 TOP 10",
        chart_hint="bar",
        description="基于已完成订单，按折后销售额识别头部商品。",
        sql="""
            SELECT
                p.product_name AS 商品,
                p.category AS 品类,
                ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate)), 2) AS 销售额,
                SUM(oi.quantity) AS 销量
            FROM order_items AS oi
            JOIN orders AS o ON o.order_id = oi.order_id
            JOIN products AS p ON p.product_id = oi.product_id
            WHERE o.status = '已完成'
            GROUP BY p.product_id, p.product_name, p.category
            ORDER BY 销售额 DESC
            LIMIT 10
        """,
    ),
    DemoQuery(
        question="各品类的销售额和利润对比",
        title="品类经营表现",
        chart_hint="bar",
        description="比较各品类折后销售额与估算毛利润。",
        sql="""
            SELECT
                p.category AS 品类,
                ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate)), 2) AS 销售额,
                ROUND(SUM(oi.quantity * (oi.unit_price * (1 - oi.discount_rate) - p.cost_price)), 2) AS 毛利润,
                ROUND(
                    100.0 * SUM(oi.quantity * (oi.unit_price * (1 - oi.discount_rate) - p.cost_price))
                    / SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate)), 2
                ) AS 毛利率
            FROM order_items AS oi
            JOIN orders AS o ON o.order_id = oi.order_id
            JOIN products AS p ON p.product_id = oi.product_id
            WHERE o.status = '已完成'
            GROUP BY p.category
            ORDER BY 销售额 DESC
        """,
    ),
    DemoQuery(
        question="各地区的客户数和销售额如何？",
        title="地区销售贡献",
        chart_hint="bar",
        description="从客户归属地区观察客户覆盖与销售贡献。",
        sql="""
            SELECT
                c.region AS 地区,
                COUNT(DISTINCT c.customer_id) AS 成交客户数,
                COUNT(DISTINCT o.order_id) AS 订单量,
                ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate)), 2) AS 销售额
            FROM customers AS c
            JOIN orders AS o ON o.customer_id = c.customer_id
            JOIN order_items AS oi ON oi.order_id = o.order_id
            WHERE o.status = '已完成'
            GROUP BY c.region
            ORDER BY 销售额 DESC
        """,
    ),
    DemoQuery(
        question="不同销售渠道的订单量和客单价",
        title="渠道效率对比",
        chart_hint="bar",
        description="比较各渠道已完成订单的规模与平均订单金额。",
        sql="""
            WITH order_totals AS (
                SELECT
                    o.order_id,
                    o.channel,
                    SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate)) AS amount
                FROM orders AS o
                JOIN order_items AS oi ON oi.order_id = o.order_id
                WHERE o.status = '已完成'
                GROUP BY o.order_id, o.channel
            )
            SELECT
                channel AS 渠道,
                COUNT(*) AS 订单量,
                ROUND(SUM(amount), 2) AS 销售额,
                ROUND(AVG(amount), 2) AS 客单价
            FROM order_totals
            GROUP BY channel
            ORDER BY 销售额 DESC
        """,
    ),
    DemoQuery(
        question="复购客户比例是多少？",
        title="客户复购分析",
        chart_hint="bar",
        description="将有 2 笔及以上已完成订单的客户定义为复购客户。",
        sql="""
            WITH customer_orders AS (
                SELECT customer_id, COUNT(*) AS order_count
                FROM orders
                WHERE status = '已完成'
                GROUP BY customer_id
            )
            SELECT
                CASE WHEN order_count >= 2 THEN '复购客户' ELSE '仅购一次' END AS 客户类型,
                COUNT(*) AS 客户数,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS 客户占比
            FROM customer_orders
            GROUP BY CASE WHEN order_count >= 2 THEN '复购客户' ELSE '仅购一次' END
            ORDER BY 客户数 DESC
        """,
    ),
)

DEMO_QUERY_MAP = {item.question: item for item in DEMO_QUERIES}


def get_demo_query(question: str) -> DemoQuery:
    try:
        return DEMO_QUERY_MAP[question]
    except KeyError as exc:
        raise ValueError("体验模式仅支持界面中列出的预设问题。") from exc

