import sqlite3
import json
import os
from datetime import datetime

# 🔁 Пути
DB_PATH = "/home/anastasia/project.db"
JSON_PATH = "/home/anastasia/PycharmProjects/medguides/parser/usa-parser/icd10cm_us_pdf_guideline_index.json"
REAL_PDF_DIR = "/home/anastasia/PycharmProjects/medguides/parser/usa-parser/usa_pdf"

# Подключение к БД
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Загружаем JSON
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

inserted = 0

for record in data:
    rec_id = record.get("rec_id")
    title = record.get("title")
    country = record.get("country", "USA")  # если нет, будет "USA"
    source = record.get("source", "")       # может быть пустым
    mkb_codes = json.dumps(eval(record.get("mkb_codes", "[]")))
    mkb_11 = "[]"
    mkb_mapping = "{}"
    json_content = None

    # 🛠 Исправляем путь
    filename = os.path.basename(record["pdf_path"])
    real_pdf_path = os.path.join(REAL_PDF_DIR, filename)

    if not os.path.exists(real_pdf_path):
        print(f"❌ Не найден PDF-файл: {real_pdf_path}")
        continue

    created = datetime.now().isoformat(timespec="seconds")

    # 📥 Вставляем в БД
    cursor.execute("""
        INSERT INTO recommendations (
            rec_id, title, country, mkb_codes, mkb_11,
            mkb_mapping, json_content, pdf_path, created
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rec_id, title, country, mkb_codes, mkb_11,
        mkb_mapping, json_content, real_pdf_path, created
    ))

    inserted += 1

conn.commit()
conn.close()
print(f"✅ Загружено {inserted} рекомендаций.")
