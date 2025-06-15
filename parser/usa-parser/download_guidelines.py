import os
import json
import requests
from pathlib import Path
from urllib.parse import urlparse
from time import sleep
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INPUT_JSON = "/home/anastasia/PycharmProjects/medguides/parser/usa-parser/icd10cm_us_guideline_links.json"
OUTPUT_JSON = "us_guidelines_with_pdf_paths.json"
PDF_DIR = Path("usa")
PDF_DIR.mkdir(parents=True, exist_ok=True)

MAX_RETRIES = 3
TIMEOUT = 60
RETRY_DELAY = 2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

def download_with_retries(url, filepath, filename):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f" Попытка {attempt}: {filename}")
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            response.raise_for_status()

            if b"%PDF" not in response.content[:1024]:
                print(f" Это не PDF: {url}")
                return False

            with open(filepath, "wb") as f_out:
                f_out.write(response.content)
            print(f"Скачан: {filename}")
            return True

        except requests.exceptions.RequestException as e:
            print(f"Ошибка: {url} ({e})")
            if attempt < MAX_RETRIES:
                print("Пауза перед повтором...")
                sleep(RETRY_DELAY)
            else:
                print(f"Пропущен после {MAX_RETRIES} попыток: {filename}")
                return False


with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)
result = []
for item in data:
    url = item.get("pdf_path")
    if not url or not url.endswith(".pdf"):
        continue

    icd = item["rec_id"].replace("USA_", "")
    title = item["title"].replace(" ", "_").replace("/", "_")[:50]
    filename = f"{icd}_{title}.pdf"
    filepath = PDF_DIR / filename

    if not filepath.exists():
        success = download_with_retries(url, filepath, filename)
        if not success:
            continue
        sleep(1)

    domain = urlparse(url).netloc
    result.append({
        "rec_id": item["rec_id"],
        "title": item["title"],
        "mkb_codes": item["mkb_codes"],
        "pdf_path": str(filepath),
        "source": domain,
        "country": item.get("country", "USA")
    })

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\n Готово! Скачано и обработано: {len(result)} файлов. JSON сохранён {OUTPUT_JSON}")
