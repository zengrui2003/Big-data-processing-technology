# -*- coding: utf-8 -*-
"""
数据可视化
作者：zengrui
功能：基于清洗后的豆瓣图书数据（或 PySpark 分析结果）使用 matplotlib 生成可视化图表。
说明：可在本地运行，读取清洗后的 CSV 直接出图；图表用于报告"数据可视化"部分。
输出：在 ../data/figures_zengrui/ 下生成多张 PNG 图。
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os

# 中文显示设置
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
matplotlib.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(__file__)
IN_FILE = os.path.join(BASE, "..", "data", "douban_books_clean_zengrui.csv")
FIG_DIR = os.path.join(BASE, "..", "data", "figures_zengrui")
os.makedirs(FIG_DIR, exist_ok=True)


def main():
    df = pd.read_csv(IN_FILE, encoding="utf-8-sig")
    print(f"读取清洗数据 {len(df)} 行")

    # 图1：各分类图书数量柱状图
    plt.figure(figsize=(10, 6))
    cat_count = df["tag"].value_counts()
    cat_count.plot(kind="bar", color="#4C72B0")
    plt.title("各分类图书数量分布")
    plt.xlabel("分类")
    plt.ylabel("图书数量")
    plt.xticks(rotation=0)
    for i, v in enumerate(cat_count.values):
        plt.text(i, v + 5, str(v), ha="center")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig1_category_count.png"), dpi=150)
    plt.close()
    print("已生成 图1：各分类图书数量分布")

    # 图2：各分类平均评分柱状图
    plt.figure(figsize=(10, 6))
    cat_rating = df.groupby("tag")["rating"].mean().sort_values(ascending=False)
    cat_rating.plot(kind="bar", color="#55A868")
    plt.title("各分类平均评分")
    plt.xlabel("分类")
    plt.ylabel("平均评分")
    plt.ylim(cat_rating.min() - 0.3, cat_rating.max() + 0.2)
    plt.xticks(rotation=0)
    for i, v in enumerate(cat_rating.values):
        plt.text(i, v + 0.02, f"{v:.2f}", ha="center")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig2_category_avg_rating.png"), dpi=150)
    plt.close()
    print("已生成 图2：各分类平均评分")

    # 图3：评分分布直方图
    plt.figure(figsize=(10, 6))
    plt.hist(df["rating"], bins=30, color="#C44E52", edgecolor="white")
    plt.title("图书评分分布直方图")
    plt.xlabel("评分")
    plt.ylabel("频数")
    plt.axvline(df["rating"].mean(), color="black", linestyle="--",
                label=f"平均分 {df['rating'].mean():.2f}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig3_rating_hist.png"), dpi=150)
    plt.close()
    print("已生成 图3：评分分布直方图")

    # 图4：评分区间饼图
    plt.figure(figsize=(8, 8))
    bins = [0, 6, 7, 8, 9, 10]
    labels = ["6.0以下", "6.0-6.9", "7.0-7.9", "8.0-8.9", "9.0-10.0"]
    df["rating_range"] = pd.cut(df["rating"], bins=bins, labels=labels, right=False)
    range_count = df["rating_range"].value_counts().reindex(labels)
    plt.pie(range_count.values, labels=labels, autopct="%1.1f%%",
            colors=["#CCCCCC", "#8C8C8C", "#4C72B0", "#55A868", "#C44E52"],
            startangle=90)
    plt.title("评分区间占比")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig4_rating_pie.png"), dpi=150)
    plt.close()
    print("已生成 图4：评分区间占比饼图")

    # 图5：出版年份趋势（数量+平均分双轴）
    yearly = df[(df["pub_year"] >= 1990) & (df["pub_year"] <= 2026)].groupby("pub_year").agg(
        cnt=("title", "count"), avg_rating=("rating", "mean")).reset_index()
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(yearly["pub_year"], yearly["cnt"], color="#4C72B0", alpha=0.6, label="图书数量")
    ax1.set_xlabel("出版年份")
    ax1.set_ylabel("图书数量", color="#4C72B0")
    ax2 = ax1.twinx()
    ax2.plot(yearly["pub_year"], yearly["avg_rating"], color="#C44E52", marker="o", label="平均评分")
    ax2.set_ylabel("平均评分", color="#C44E52")
    plt.title("各出版年份图书数量与平均评分趋势")
    fig.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig5_year_trend.png"), dpi=150)
    plt.close()
    print("已生成 图5：出版年份趋势图")

    # 图6：评价人数 Top15 横向条形图
    plt.figure(figsize=(11, 7))
    top15 = df.nlargest(15, "rating_people")[["title", "rating_people"]]
    plt.barh(top15["title"][::-1], top15["rating_people"][::-1], color="#8172B3")
    plt.title("评价人数最多的 Top15 图书")
    plt.xlabel("评价人数")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig6_top_popular.png"), dpi=150)
    plt.close()
    print("已生成 图6：评价人数 Top15")

    print(f"\n全部图表已保存到：{os.path.abspath(FIG_DIR)}")


if __name__ == "__main__":
    main()
