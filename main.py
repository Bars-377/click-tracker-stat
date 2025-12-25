import json
import psycopg2
from urllib.parse import urlparse

# ------------------------------
# Функция для нормализации домена
# ------------------------------
def normalize_domain(url: str) -> str:
    """
    Преобразует URL в домен без протокола и www.
    """
    if not url:
        return ""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path  # если нет схемы, берем path
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.lower()

# ------------------------------
# Загружаем конфиг
# ------------------------------
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

db_config = config["db"]
search_texts = config.get("search_texts", [])
client_id = config.get("client_id", "0")
allowed_sites = [normalize_domain(s) for s in config.get("allowed_sites", [])]

if not allowed_sites:
    raise ValueError("В config.json не задан allowed_sites")

# ------------------------------
# Подключение к PostgreSQL
# ------------------------------
conn = psycopg2.connect(
    user=db_config["user"],
    password=db_config["password"],
    host=db_config["host"],
    port=db_config["port"],
    database=db_config["database"]
)

try:
    with conn.cursor() as cursor:

        # ------------------------------
        # Основной запрос по каждому тексту
        # ------------------------------
        main_query = """
            SELECT
                user_login,
                COUNT(*) AS appointment_count
            FROM clicks
            WHERE text = %s
              AND client_id = %s
            GROUP BY user_login
            ORDER BY appointment_count DESC;
        """

        for text in search_texts:
            cursor.execute(main_query, (text, client_id))
            results = cursor.fetchall()

            print(f"\nРезультаты для: '{text}'")
            print(f"{'user_login':<20} | appointment_count")
            print("-" * 35)
            for user_login, count in results:
                print(f"{user_login:<20} | {count}")

        # ------------------------------
        # Общая статистика по всем текстам (через Python)
        # ------------------------------
        cursor.execute("SELECT user_login, page_url FROM clicks WHERE client_id = %s;", (client_id,))
        rows = cursor.fetchall()

        unique_users = set()
        unique_domains = set()

        for user_login, page_url in rows:
            domain = normalize_domain(page_url)
            if domain in allowed_sites:
                unique_users.add(user_login)
                unique_domains.add(domain)

        print("\n===== ОБЩАЯ СТАТИСТИКА ПО ВСЕМ ЗАПРОСАМ =====")
        print(f"Всего уникальных user_login: {len(unique_users)}")
        print(f"Всего уникальных сайтов: {len(unique_domains)}")

finally:
    conn.close()
