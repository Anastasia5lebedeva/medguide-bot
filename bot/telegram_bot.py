from telegram import InputFile, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import tempfile
import logging
import re
import asyncio
import aiohttp
import os
import pdfplumber

API_URL = "http://api:8000"  # URL FastAPI-сервиса
MAX_TELEGRAM_LENGTH = 4096

logging.basicConfig(
    filename="bot_error.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def clean_text(text: str) -> str:
    text = re.sub(r'[^\x00-\x7Fа-яА-ЯёЁ0-9.,!?;:\-\(\)\[\]\{\}\s]', '', text)
    return re.sub(r'\s+', ' ', text.strip())

def split_text_safely(text: str, header: str, max_len=MAX_TELEGRAM_LENGTH):
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

def extract_text_from_pdf_file(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logging.error(f"Ошибка при извлечении текста: {e}")
    return clean_text(text)

async def fetch_recommendations(mkb_code: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/recommendations/{mkb_code}") as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                logging.error(f"Не удалось получить рекомендации. Код ответа: {resp.status}")
                return []

async def download_pdf(rec_id: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/pdf/{rec_id}") as resp:
            if resp.status == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(await resp.read())
                    return tmp.name
            else:
                logging.warning(f"Не удалось загрузить PDF для {rec_id}")
                return None

async def send_pdf_from_api(rec: dict, update: Update, context: ContextTypes.DEFAULT_TYPE, with_text=True):
    pdf_path = await download_pdf(rec["rec_id"])
    if not pdf_path:
        await update.message.reply_text(f"❌ Не удалось загрузить PDF: {rec['title']}")
        return

    try:
        with open(pdf_path, "rb") as pdf_file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=InputFile(pdf_file, filename=f"{rec['title'] or rec['rec_id']}.pdf"),
                caption=f"📎 Клинические рекомендации: {rec['title']}"
            )
    except Exception as e:
        logging.error(f"Ошибка отправки PDF: {e}")
        await update.message.reply_text("Ошибка при отправке PDF")

    if with_text:
        text = extract_text_from_pdf_file(pdf_path)
        chunks = split_text_safely(text, f"{rec['rec_id']} — {rec['title']}")
        for chunk in chunks:
            await update.message.reply_text(chunk)
            await asyncio.sleep(1)

    os.remove(pdf_path)

async def handle_mkb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите код МКБ: /mkb <код>")
        return

    mkb_code = context.args[0].strip().upper()
    recs = await fetch_recommendations(mkb_code)

    if not recs:
        await update.message.reply_text(f"🚫 Рекомендации по коду {mkb_code} не найдены.")
        return

    grouped = {"Россия": [], "США": [], "ВОЗ": []}
    for rec in recs:
        country = rec.get("country", "").upper()
        if "RUS" in country:
            grouped["Россия"].append(rec)
        elif "USA" in country:
            grouped["США"].append(rec)
        elif "WHO" in country:
            grouped["ВОЗ"].append(rec)

    summary_lines = ["📑 Найденные рекомендации:"]
    for country, rec_list in grouped.items():
        for rec in rec_list:
            summary_lines.append(f"- {country}: {rec['title']}")

    await update.message.reply_text("\n".join(summary_lines))

    first_text_sent = False
    for country in ["Россия", "США", "ВОЗ"]:
        for rec in grouped[country]:
            await send_pdf_from_api(rec, update, context, with_text=not first_text_sent)
            first_text_sent = True
            await asyncio.sleep(2)


def main():
    app = Application.builder().token("7743250703:AAFxxZq2ugNAK2Uf3WdPH1ngvFJ2lZKk3_M").build()
    app.add_handler(CommandHandler("mkb", handle_mkb))
    print(" Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
