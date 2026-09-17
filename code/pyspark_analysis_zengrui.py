# -*- coding: utf-8 -*-
"""
PySpark 数据分析
作者：zengrui
功能：使用 PySpark（Spark SQL + DataFrame）对存储在 HDFS 上的豆瓣图书清洗数据进行分析。
运行环境：已部署好的 Hadoop + Spark 伪分布式环境
运行方式：spark-submit pyspark_analysis_zengrui.py
         或在 pyspark shell 中逐段执行。
数据位置：HDFS 路径 /user/hadoop/douban_zengrui/douban_books_clean_zengrui.csv
说明：基于真实采集并清洗后的数据进行分析，结果导出为 CSV 供可视化使用。
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# HDFS 上清洗后数据的路径（请根据实际上传路径调整）
HDFS_INPUT = "hdfs://localhost:9000/user/hadoop/douban_zengrui/douban_books_clean_zengrui.csv"
# 分析结果导出目录（本地，用于可视化）
LOCAL_OUT = "file:///home/hadoop/douban_zengrui_result"


def main():
    spark = (SparkSession.builder
             .appName("DoubanBookAnalysis_zengrui")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")

    # ========== 读取 HDFS 上的数据 ==========
    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .csv(HDFS_INPUT))

    print("=== Schema ===")
    df.printSchema()
    total = df.count()
    print(f"=== 总记录数：{total} ===")

    # 注册临时视图，使用 Spark SQL
    df.createOrReplaceTempView("books")

    # ---------- 分析1：各标签（分类）图书数量分布 ----------
    print("\n=== 分析1：各分类图书数量 ===")
    cat_count = spark.sql("""
        SELECT tag, COUNT(*) AS book_count
        FROM books
        GROUP BY tag
        ORDER BY book_count DESC
    """)
    cat_count.show(truncate=False)

    # ---------- 分析2：各分类平均评分 ----------
    print("\n=== 分析2：各分类平均评分 ===")
    cat_rating = spark.sql("""
        SELECT tag,
               ROUND(AVG(rating), 2) AS avg_rating,
               ROUND(MAX(rating), 2) AS max_rating,
               ROUND(MIN(rating), 2) AS min_rating
        FROM books
        GROUP BY tag
        ORDER BY avg_rating DESC
    """)
    cat_rating.show(truncate=False)

    # ---------- 分析3：评分区间分布 ----------
    print("\n=== 分析3：评分区间分布 ===")
    rating_dist = spark.sql("""
        SELECT
            CASE
                WHEN rating >= 9 THEN '9.0-10.0'
                WHEN rating >= 8 THEN '8.0-8.9'
                WHEN rating >= 7 THEN '7.0-7.9'
                WHEN rating >= 6 THEN '6.0-6.9'
                ELSE '6.0以下'
            END AS rating_range,
            COUNT(*) AS cnt
        FROM books
        GROUP BY 1
        ORDER BY rating_range DESC
    """)
    rating_dist.show(truncate=False)

    # ---------- 分析4：评价人数 Top20 的热门图书 ----------
    print("\n=== 分析4：评价人数最多的 Top20 图书 ===")
    top_popular = spark.sql("""
        SELECT title, author, rating, rating_people
        FROM books
        ORDER BY rating_people DESC
        LIMIT 20
    """)
    top_popular.show(truncate=False)

    # ---------- 分析5：高分图书（评分>=9 且评价人数>=1000）Top20 ----------
    print("\n=== 分析5：高口碑图书 Top20（评分>=9 且 评价人数>=1000）===")
    top_rated = spark.sql("""
        SELECT title, author, rating, rating_people
        FROM books
        WHERE rating >= 9 AND rating_people >= 1000
        ORDER BY rating DESC, rating_people DESC
        LIMIT 20
    """)
    top_rated.show(truncate=False)

    # ---------- 分析6：按出版年份统计图书数量与平均评分 ----------
    print("\n=== 分析6：各出版年份图书数量与平均评分（近年）===")
    year_stat = spark.sql("""
        SELECT pub_year,
               COUNT(*) AS cnt,
               ROUND(AVG(rating), 2) AS avg_rating
        FROM books
        WHERE pub_year IS NOT NULL AND pub_year BETWEEN 1990 AND 2026
        GROUP BY pub_year
        ORDER BY pub_year
    """)
    year_stat.show(50, truncate=False)

    # ========== 使用 RDD 进行词频统计（作者出现次数）==========
    print("\n=== 分析7：高产作者 Top20（RDD 词频统计）===")
    author_rdd = (df.select("author").rdd
                  .map(lambda r: (r["author"] or "未知").strip())
                  .filter(lambda a: a and a != "未知")
                  .map(lambda a: (a, 1))
                  .reduceByKey(lambda x, y: x + y)
                  .sortBy(lambda x: -x[1]))
    for author, cnt in author_rdd.take(20):
        print(f"  {author}: {cnt} 本")

    # ========== 导出分析结果到本地，供可视化使用 ==========
    print("\n=== 导出分析结果 ===")
    cat_count.coalesce(1).write.mode("overwrite").option("header", "true").csv(LOCAL_OUT + "/cat_count")
    cat_rating.coalesce(1).write.mode("overwrite").option("header", "true").csv(LOCAL_OUT + "/cat_rating")
    rating_dist.coalesce(1).write.mode("overwrite").option("header", "true").csv(LOCAL_OUT + "/rating_dist")
    year_stat.coalesce(1).write.mode("overwrite").option("header", "true").csv(LOCAL_OUT + "/year_stat")
    top_popular.coalesce(1).write.mode("overwrite").option("header", "true").csv(LOCAL_OUT + "/top_popular")
    print(f"结果已导出到：{LOCAL_OUT}")

    spark.stop()


if __name__ == "__main__":
    main()
