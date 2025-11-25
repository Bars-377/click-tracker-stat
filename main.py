import json
import psycopg2

# Загружаем конфиг
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

db_config = config["db"]
search_texts = config.get("search_texts", ["Запись на приём к врачу"])

# Подключение к PostgreSQL
conn = psycopg2.connect(
    user=db_config["user"],
    password=db_config["password"],
    host=db_config["host"],
    port=db_config["port"],
    database=db_config["database"]
)

try:
    with conn.cursor() as cursor:
        query = """
            SELECT
                user_login,
                COUNT(*) AS appointment_count
            FROM
                clicks
            WHERE
                text = %s
            GROUP BY
                user_login
            ORDER BY
                appointment_count DESC;
        """
        for text in search_texts:
            cursor.execute(query, (text,))
            results = cursor.fetchall()
            print(f"\nРезультаты для: '{text}'")
            print(f"{'user_login':<20} | {'appointment_count'}")
            print("-" * 35)
            for row in results:
                print(f"{row[0]:<20} | {row[1]}")
finally:
    conn.close()
