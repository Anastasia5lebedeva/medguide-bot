import pandas as pd
import requests
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

LOG_FILE = "/home/anastasia/PycharmProjects/medguides/parser/ru-parser/pdf_download_log.txt"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")


EXCEL_FILE = "/home/anastasia/PycharmProjects/medguides/parser/ru-parser/Список утвержденных клинических рекомендаций.xlsx"
PDF_DIR = "/home/anastasia/PycharmProjects/medguides/parser/ru-parser/pdf"
os.makedirs(PDF_DIR, exist_ok=True)


def sanitize_filename(text):
    text = text[:150]
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in text).strip()


def download_pdf(rec_id, title):
    url = f"https://apicr.minzdrav.gov.ru/api.ashx?op=GetClinrecPdf&id={rec_id}"
    filename = f"{sanitize_filename(title)}_{rec_id}.pdf"
    path = os.path.join(PDF_DIR, filename)

    if os.path.exists(path):
        logging.info(f"[✓] PDF уже существует: {filename}")
        return f"[✓] PDF уже существует: {filename}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200 and "application/pdf" in response.headers.get("Content-Type", ""):
            with open(path, "wb") as f:
                f.write(response.content)
            logging.info(f" PDF скачан: {filename}")
            return f" PDF скачан: {filename}"
        else:
            logging.warning(f"PDF не найден для {rec_id} (статус {response.status_code})")
            return f" PDF не найден для {rec_id} (статус {response.status_code})"
    except Exception as e:
        logging.error(f" Ошибка PDF для {rec_id}: {e}")
        return f" Ошибка PDF для {rec_id}: {e}"


def main():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name="Лист1")
        if df.empty:
            logging.error("Excel-файл пустой")
            print("Excel-файл пустой")
            return

        total_recs = len(df)
        print(f"Найдено {total_recs} рекомендаций")

        tasks = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for i, row in df.iterrows():
                rec_id = str(row["ID"]).strip()
                title = str(row["Наименование"]).strip()
                if not rec_id or not title:
                    logging.warning(f"Пропущена строка {i + 1}: пустой ID или название")
                    continue
                tasks.append(executor.submit(download_pdf, rec_id, title))

            for i, future in enumerate(as_completed(tasks), 1):
                print(future.result())
                print(f"Обработано {i}/{total_recs} ({i / total_recs * 100:.2f}%)")
                sleep(0.1)

        logging.info("Завершено скачивание PDF")
        print("Завершено скачивание PDF")
    except Exception as e:
        logging.error(f"Ошибка обработки Excel: {e}")
        print(f"Ошибка обработки Excel: {e}")


if __name__ == "__main__":
    main()