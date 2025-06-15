import json
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

INPUT_JSON = "/home/anastasia/PycharmProjects/medguides/parser/who_guidelines_filtered.json"
PDF_DIR = "/parser/who-parser/who_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

for entry in tqdm(data, desc="Скачивание PDF"):
    title = entry.get("title")
    page_url = entry.get("source_url")

    try:
        print(f" Открываю: {title}")
        driver.get(page_url)
        time.sleep(3)

        link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.pdf') and contains(., '.pdf')]"))
        )
        pdf_url = link.get_attribute("href")

        headers_pdf = {
            "User-Agent": "Mozilla/5.0",
            "Referer": page_url,
            "Accept": "application/pdf"
        }
        response = requests.get(pdf_url, headers=headers_pdf, timeout=30)

        if response.status_code == 200 and b"%PDF" in response.content[:10]:
            filename = pdf_url.split("/")[-1].split("?")[0]
            file_path = os.path.join(PDF_DIR, filename)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f" Скачан: {filename}")
        else:
            print(f" Ошибка: {title} — Файл не является PDF")

    except Exception as e:
        print(f" Ошибка: {title} — {e}")
driver.quit()
