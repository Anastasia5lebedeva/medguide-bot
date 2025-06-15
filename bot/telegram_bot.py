from telegram import Update, Document
from telegram.ext import Application, CommandHandler, ContextTypes
import pdfplumber
import os
import asyncio
import re
import logging
import json
from pdf2image import convert_from_path
import pytesseract

# Настройка логирования
logging.basicConfig(
    filename="bot_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

JSON_FILE = "/home/anastasia/PycharmProjects/medguides/parser/ru-parser/russian_guidelines.json"
MAX_TELEGRAM_LENGTH = 4096




def clean_text(text):
    text = re.sub(r'[^\x00-\x7Fа-яА-ЯёЁ0-9.,!?;:\-\(\)\[\]\{\}\s]', '', text)
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def split_text_safely(text, header, max_len=MAX_TELEGRAM_LENGTH):
    chunks = []
    chunk_len = max_len - len(header) - 50
    i = 0
    while i < len(text):
        next_chunk = text[i:i+chunk_len]
        last_dot = max(next_chunk.rfind("."), next_chunk.rfind("\n"), next_chunk.rfind(";"))
        if last_dot == -1 or i + last_dot + 1 >= len(text):
            last_dot = chunk_len
        chunks.append(text[i:i+last_dot+1].strip())
        i += last_dot + 1
    return chunks


def search_icd_in_pdf_ocr(icd_code, pdf_path):
    try:
        pages = convert_from_path(pdf_path, dpi=200)
        full_text = ""
        for page in pages:
            text = pytesseract.image_to_string(page, lang='rus+eng')
            full_text += text + "\n"
            if icd_code in text:
                return True, clean_text(full_text)
        return False, None
    except Exception as e:
        logging.error(f"OCR ошибка в {pdf_path}: {e}")
        return False, None

# Основной обработчик
async def handle_icd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажите код МКБ: /icd <код>")
        return

    query_code = context.args[0].strip().upper()

    if not os.path.exists(JSON_FILE):
        await update.message.reply_text("❌ JSON-файл не найден.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = []
    for entry in data:
        codes = entry.get("mkb_codes") or entry.get("mkb") or []
        if isinstance(codes, str):
            codes = [codes]
        if any(code.strip().upper().startswith(query_code) for code in codes):
            matches.append(entry)

    if not matches:
        await update.message.reply_text(f"❌ В JSON нет записей по коду {query_code}. Ищу в PDF через OCR...")

        for entry in data:
            pdf_path = entry.get("pdf_path") or entry.get("pdf")
            if pdf_path and os.path.exists(pdf_path):
                found, ocr_text = search_icd_in_pdf_ocr(query_code, pdf_path)
                if found:
                    title = entry.get("title", "Без названия")
                    header = f" {query_code} — {title}"
                    await update.message.reply_text(f"🔍 Найдено в PDF через OCR: {header}")
                    chunks = split_text_safely(ocr_text, header)
                    for i, chunk in enumerate(chunks, 1):
                        await update.message.reply_text(f"{header} (Часть {i}/{len(chunks)}):\n{chunk}")
                        await asyncio.sleep(1)
                    return

        await update.message.reply_text("❌ Даже через OCR ничего не найдено.")
        return

    # Есть совпадения в JSON
    match = matches[0]
    icd = match.get("mkb_codes", [None])[0]
    title = match.get("title", "Без названия")
    pdf_path = match.get("pdf_path") or match.get("pdf")

    if not pdf_path or not os.path.exists(pdf_path):
        await update.message.reply_text(f"⚠️ PDF-файл для {icd} не найден.")
        return

    try:
        with open(pdf_path, "rb") as f:
            await update.message.reply_document(f, filename=os.path.basename(pdf_path))
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF {pdf_path}: {e}")
        await update.message.reply_text("⚠️ Не удалось прикрепить PDF.")

    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        header = f" {icd} — {title}"
        chunks = split_text_safely(clean_text(text), header)

        for i, chunk in enumerate(chunks, 1):
            await update.message.reply_text(f"{header} (Часть {i}/{len(chunks)}):\n{chunk}")
            await asyncio.sleep(1)

    except Exception as e:
        logging.error(f"Ошибка при обработке PDF {pdf_path}: {e}")
        await update.message.reply_text(f"❌ Ошибка при обработке PDF: {e}")

# Запуск

def main():
    app = Application.builder().token("7743250703:AAFxxZq2ugNAK2Uf3WdPH1ngvFJ2lZKk3_M").build()
    app.add_handler(CommandHandler("mkb", handle_icd))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()