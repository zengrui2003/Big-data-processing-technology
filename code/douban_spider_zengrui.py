# -*- coding: utf-8 -*-
"""
豆瓣图书评分数据爬虫
作者：zengrui
功能：按多个标签翻页爬取豆瓣图书的真实图书评分数据，目标 >= 5000 行
说明：真实抓取，不编造数据。含随机延时、UA 轮换、失败重试，遵守基本爬取礼仪。
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import csv
import time
import random
import re
import os

# 输出文件（文件名按试题要求在原名后加姓名拼音全拼）
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "douban_books_raw_zengrui.csv")

# 多个标签，每个标签可翻 50 页（1000 本），凑够 5000+ 行
TAGS = ["小说", "历史", "科技", "经济", "心理学", "计算机", "传记"]

# User-Agent 轮换池
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
]


def make_headers():
    return {
        "User-Agent": random.choice(UA_POOL),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://book.douban.com/",
    }


def fetch(url, max_retry=3):
    """带重试的请求"""
    for attempt in range(1, max_retry + 1):
        try:
            r = requests.get(url, headers=make_headers(), timeout=15)
            if r.status_code == 200:
                return r.text
            print(f"  [警告] {url} 返回 {r.status_code}，第 {attempt} 次重试")
        except Exception as e:
            print(f"  [异常] {url} {e}，第 {attempt} 次重试")
        time.sleep(random.uniform(3, 6))
    return None


def parse_pub(text):
    """解析 '作者 / 出版社 / 出版日期 / 价格' 字段"""
    parts = [p.strip() for p in text.split("/")]
    author = parts[0] if len(parts) >= 1 else ""
    publisher = parts[-3] if len(parts) >= 3 else ""
    pub_date = parts[-2] if len(parts) >= 2 else ""
    price = parts[-1] if len(parts) >= 2 else ""
    return author, publisher, pub_date, price


def parse_page(html, tag):
    """解析单页，返回图书记录列表"""
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for it in soup.select("li.subject-item"):
        a = it.select_one("h2 a")
        if not a:
            continue
        title = (a.get("title") or a.get_text(strip=True)).strip()
        link = a.get("href", "").strip()

        pub_el = it.select_one("div.pub")
        author = publisher = pub_date = price = ""
        if pub_el:
            author, publisher, pub_date, price = parse_pub(pub_el.get_text(strip=True))

        rating_el = it.select_one("span.rating_nums")
        rating = rating_el.get_text(strip=True) if rating_el else ""

        people_el = it.select_one("span.pl")
        people = ""
        if people_el:
            m = re.search(r"(\d+)", people_el.get_text())
            people = m.group(1) if m else ""

        rows.append({
            "tag": tag,
            "title": title,
            "author": author,
            "publisher": publisher,
            "pub_date": pub_date,
            "price": price,
            "rating": rating,
            "rating_people": people,
            "url": link,
        })
    return rows


def main():
    all_rows = []
    seen = set()  # 去重（同一本书可能出现在多个标签）
    fieldnames = ["tag", "title", "author", "publisher", "pub_date",
                  "price", "rating", "rating_people", "url"]

    for tag in TAGS:
        print(f"\n===== 开始爬取标签：{tag} =====")
        empty_streak = 0
        for page in range(0, 50):  # 最多 50 页
            start = page * 20
            url = f"https://book.douban.com/tag/{quote(tag)}?start={start}&type=T"
            html = fetch(url)
            if not html:
                print(f"  start={start} 获取失败，跳过")
                continue
            rows = parse_page(html, tag)
            if not rows:
                empty_streak += 1
                if empty_streak >= 2:
                    print(f"  连续空页，结束标签 {tag}")
                    break
                continue
            empty_streak = 0
            added = 0
            for row in rows:
                key = row["url"] or row["title"]
                if key in seen:
                    continue
                seen.add(key)
                all_rows.append(row)
                added += 1
            print(f"  start={start:<4} 本页 {len(rows)} 条，新增 {added} 条，累计 {len(all_rows)} 条")
            # 随机延时，降低被封风险
            time.sleep(random.uniform(2.5, 5.0))
        # 已达标可提前停止
        if len(all_rows) >= 5200:
            print(f"\n已采集 {len(all_rows)} 条，达到目标，停止。")
            break

    # 写 CSV
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n===== 完成 =====")
    print(f"共采集 {len(all_rows)} 条真实图书数据")
    print(f"已保存到：{os.path.abspath(OUT_FILE)}")


if __name__ == "__main__":
    main()
