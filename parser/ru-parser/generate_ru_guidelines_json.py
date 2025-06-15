import pandas as pd
import json
import os
import logging
from pathlib import Path

LOG_FILE = "/home/anastasia/PycharmProjects/medguides/parser/map_ru_log.txt"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

EXCEL_FILE = "/home/anastasia/PycharmProjects/medguides/parser/ru-parser/Список утвержденных клинических рекомендаций.xlsx"
PDF_DIR = "/home/anastasia/PycharmProjects/medguides/parser/ru-parser/pdf"
JSON_OUTPUT = "/home/anastasia/PycharmProjects/medguides/parser/ru-parser/russian_guidelines.json"

# Создаём папку для JSON
Path(JSON_OUTPUT).parent.mkdir(parents=True, exist_ok=True)

def clean_text(text):
    if not text or text.strip() in ["", "Информация отсутствует"]:
        return None
    return text.strip()

def find_pdf(rec_id, title):
    title_clean = title.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").replace(":", "").replace("/", "_")
    for filename in os.listdir(PDF_DIR):
        filename_clean = filename.lower().replace(" ", "_")
        if rec_id in filename or (title_clean in filename_clean and rec_id in filename) and filename.endswith(".pdf"):
            return os.path.join(PDF_DIR, filename)
    return None

def main():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name="Лист1")
        if df.empty:
            logging.error("Excel пустой")
            print("Excel пустой")
            return

        data = []
        for _, row in df.iterrows():
            rec_id = str(row["ID"]).strip()
            title = clean_text(row["Наименование"])
            mkb_codes = clean_text(row["МКБ-10"])
            mkb_codes = [code.strip() for code in mkb_codes.split(",") if code.strip()] if mkb_codes else []

            if not rec_id or not title:
                logging.warning(f"Пропущена строка: пустой ID или название")
                continue

            pdf_path = find_pdf(rec_id, title)
            if not pdf_path:
                logging.warning(f"PDF не найден для rec_id: {rec_id}")
                print(f"PDF не найден для rec_id: {rec_id}")
                continue

            rec_data = {
                "rec_id": rec_id,
                "title": title,
                "mkb_codes": mkb_codes,
                "pdf_path": pdf_path
            }
            data.append(rec_data)

        with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f" JSON сохранён: {JSON_OUTPUT}")
        print(f" JSON сохранён: {JSON_OUTPUT}")
        print(f"Обработано {len(data)} записей")

    except Exception as e:
        logging.error(f"Ошибка обработки: {e}")
        print(f"Ошибка обработки: {e}")

if __name__ == "__main__":
    main()
