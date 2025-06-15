import json
import re
import requests
from pathlib import Path
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

INPUT_FILE  = "/home/anastasia/PycharmProjects/medguides/parser/usa-parser/us_icd10cm_codes_for_guidelines.json"
OUTPUT_FILE = "us_guideline_links.json"
NOT_FOUND_FILE = "us_guideline_links_not_found.json"
HEADLESS = True
GOOD_KW = [
    "guideline", "guidelines", "clinical practice guideline", "cpg",
    "recommendation", "recommendations", "practice parameter",
    "consensus report", "policy statement", "management", "algorithm",
]
BAD_KW = [
    "fact sheet", "patient", "brochure", "leaflet", "slides", "poster",
    "training", "course", "newsletter", "case report", "review article",
]
DOMAINS = ["cdc.gov", "ahrq.gov", "nccn.org", "nih.gov", "ada.org", "pmc.ncbi.nlm.nih.gov"]
TIERS   = ["clinical guideline", "guideline", "recommendation", "treatment"]
WAIT = 2

def url_is_pdf(href: str) -> bool:
    return href.lower().endswith(".pdf")

def good_title(title: str) -> bool:
    tl = title.lower()
    return any(kw in tl for kw in GOOD_KW) and not any(sw in tl for sw in BAD_KW)

def good_html(href: str, title: str) -> bool:
    return (not url_is_pdf(href)
            and any(dom in href for dom in DOMAINS)
            and good_title(title))

def pdf_from_html(page_url: str) -> str | None:
    try:
        r = requests.get(page_url, timeout=15)
        if not r.ok:
            return None
        html = r.text
        m = re.search(r'<meta[^>]+citation_pdf_url\s*content=["\']([^"\']+\.pdf)["\']', html, re.I)
        if m:
            return m.group(1)
        m = re.search(r'href=["\']([^"\']+\.pdf)["\']', html, re.I)
        return m.group(1) if m else None
    except requests.RequestException:
        return None

def make_driver():
    opts = webdriver.ChromeOptions()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=webdriver.chrome.service.Service(
        ChromeDriverManager().install()), options=opts)

def bing_links(driver, query: str):
    driver.get("https://www.bing.com/")
    box = driver.find_element(By.NAME, "q")
    box.clear(); box.send_keys(query); box.send_keys(Keys.RETURN)
    sleep(1.5)
    return driver.find_elements(By.XPATH, '//li[@class="b_algo"]//a')

with open(INPUT_FILE, encoding="utf-8") as f:
    diseases = json.load(f)

results, not_found = [], []
driver = make_driver()

total, found_cnt = len(diseases), 0

for idx, (code, disease) in enumerate(tqdm(diseases.items(), desc="ICD"), 1):
    found = False

    for tier in TIERS:
        if found:
            break
        for dom in DOMAINS + [""]:
            if found:
                break
            site = f" site:{dom}" if dom else ""
            for q in [f'{code} "{disease}" {tier}{site} filetype:pdf',
                      f'{code} "{disease}" {tier}{site}']:
                try:
                    links = bing_links(driver, q)
                except (WebDriverException, NoSuchElementException):
                    continue

                for lk in links:
                    href = lk.get_attribute("href") or ""
                    title = lk.text or ""
                    if url_is_pdf(href) and good_title(title):
                        results.append({
                            "icd_code": code,
                            "title": disease,
                            "keyword": tier,
                            "url": href,
                            "format": "pdf",
                            "source": "USA",
                            "language": "en"
                        })
                        print(f"[{idx}/{total}] [+] PDF для {code}: {href}")
                        found = True; found_cnt += 1
                        break
                    if good_html(href, title):
                        pdf_inside = pdf_from_html(href)
                        if pdf_inside and url_is_pdf(pdf_inside):
                            results.append({
                                "icd_code": code,
                                "title": disease,
                                "keyword": tier,
                                "url": pdf_inside,
                                "format": "pdf",
                                "via": href,
                                "source": "USA",
                                "language": "en"
                            })
                            print(f"[{idx}/{total}] PDF внутри HTML для {code}: {pdf_inside}")
                            found = True; found_cnt += 1
                            break
                        else:
                            results.append({
                                "icd_code": code,
                                "title": disease,
                                "keyword": tier,
                                "url": href,
                                "format": "html",
                                "source": "USA",
                                "language": "en"
                            })
                            print(f"[{idx}/{total}] HTML для {code}: {href}")
                            found = True; found_cnt += 1
                            break
                if found:
                    break

    if not found:
        print(f"[{idx}/{total}] [!] НЕ найден клинрек для {code}")
        not_found.append({"icd_code": code, "title": disease})
    sleep(WAIT)

Path(OUTPUT_FILE).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
Path(NOT_FOUND_FILE).write_text(json.dumps(not_found, ensure_ascii=False, indent=2), encoding="utf-8")
driver.quit()
print(f"\nИтого: найдено {found_cnt} клинреков из {total} кодов.")
print(f"Файл с найденными: {OUTPUT_FILE}")
print(f"Файл с пропущенными: {NOT_FOUND_FILE}")
