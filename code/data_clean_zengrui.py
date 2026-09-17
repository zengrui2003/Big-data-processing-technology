# -*- coding: utf-8 -*-
"""
数据清洗与格式转换
作者：zengrui
功能：对爬取的豆瓣图书原始数据进行清洗——去脏数据、类型转换、去重、缺失处理，
      并转换为干净的 CSV，供后续存入 HDFS 和 PySpark 分析使用。
说明：真实数据清洗，无编造。
"""
import pandas as pd
import os
import re

BASE = os.path.dirname(__file__)
IN_FILE = os.path.join(BASE, "..", "data", "douban_books_raw_zengrui.csv")
OUT_FILE = os.path.join(BASE, "..", "data", "douban_books_clean_zengrui.csv")


def clean_year(pub_date):
    """从出版日期中提取年份（4 位数字）"""
    if pd.isna(pub_date):
        return None
    m = re.search(r"(19|20)\d{2}", str(pub_date))
    return int(m.group(0)) if m else None


def clean_price(price):
    """从价格字段提取数值（去掉币种符号、元字等）"""
    if pd.isna(price):
        return None
    m = re.search(r"(\d+\.?\d*)", str(price).replace(",", ""))
    return float(m.group(1)) if m else None


def main():
    print(f"读取原始数据：{IN_FILE}")
    df = pd.read_csv(IN_FILE, encoding="utf-8-sig")
    print(f"原始记录数：{len(df)}")

    # 1. 去重（按 url 去重，url 为空则按标题）
    df["dedup_key"] = df["url"].fillna("").where(df["url"].fillna("") != "", df["title"])
    df = df.drop_duplicates(subset=["dedup_key"]).drop(columns=["dedup_key"])
    print(f"去重后：{len(df)}")

    # 2. 评分转数值，剔除无评分/异常评分的脏数据
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df[df["rating"].notna()]
    df = df[(df["rating"] >= 0) & (df["rating"] <= 10)]
    print(f"剔除无效评分后：{len(df)}")

    # 3. 评价人数转整数
    df["rating_people"] = pd.to_numeric(df["rating_people"], errors="coerce").fillna(0).astype(int)

    # 4. 出版年份提取
    df["pub_year"] = df["pub_date"].apply(clean_year)

    # 5. 价格提取为数值
    df["price_num"] = df["price"].apply(clean_price)

    # 6. 去掉书名为空的脏数据，并清理标题首尾空白
    df["title"] = df["title"].astype(str).str.strip()
    df = df[df["title"] != ""]

    # 7. 过滤评价人数过少的（噪声数据，评价人数 < 10 视为不可靠）
    before = len(df)
    df = df[df["rating_people"] >= 10]
    print(f"剔除评价人数<10 的记录 {before - len(df)} 条，剩余：{len(df)}")

    # 8. 选取并排列最终字段
    cols = ["tag", "title", "author", "publisher", "pub_year",
            "price_num", "rating", "rating_people"]
    df = df[cols].rename(columns={"price_num": "price"})

    # 9. 重置索引并保存
    df = df.reset_index(drop=True)
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    df.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\n清洗完成，最终记录数：{len(df)}")
    print(f"已保存到：{os.path.abspath(OUT_FILE)}")
    print("\n数据预览：")
    print(df.head(10).to_string())
    print("\n字段统计：")
    print(df.describe(include='all').to_string())


if __name__ == "__main__":
    main()
