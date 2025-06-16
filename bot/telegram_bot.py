from telegram import InputFile, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.api import extract_text_from_pdf_bytes  # ✅ Путь правильный
from recommendations_db import search_recommendations_by_icd
import os
import asyncio
import re
import tempfile
import logging
import aiosqlite

logging.basicConfig(
    filename="bot_error.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_TELEGRAM_LENGTH = 4096
DB_PATH = "/home/anastasia/project.db"

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
async def send_pdf_from_db(rec_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM recommendations WHERE rec_id = ?", (rec_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await update.message.reply_text("❌ PDF не найден.")
                return

            pdf_blob = row["pdf_blob"]
            title = row["title"] or rec_id

            if pdf_blob:
                extracted_text = extract_text_from_pdf_bytes(pdf_blob)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_blob)
                    tmp_path = tmp.name

                with open(tmp_path, "rb") as pdf_file:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=InputFile(pdf_file, filename=f"{title}.pdf"),
                        caption=f"Клинические рекомендации: {title}"
                    )

                os.remove(tmp_path)

                if extracted_text:
                    chunks = split_text_safely(extracted_text, f"{rec_id} — {title}")
                    for part in chunks:
                        await update.message.reply_text(part)
                        await asyncio.sleep(1)
            else:
                await update.message.reply_text("PDF-файл отсутствует.")

async def handle_mkb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите код МКБ: /mkb <код>")
        return

    query_code = context.args[0].strip().upper()
    recs = await search_recommendations_by_icd(query_code)

    if not recs:
        await update.message.reply_text(f"Нет рекомендаций по коду {query_code}")
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

    summary_lines = ["Рекомендации найдены:"]
    for country, recs_list in grouped.items():
        for rec in recs_list:
            title = rec.get("title", "Без названия")
            summary_lines.append(f"- {country}: {title}")

    await update.message.reply_text("\n".join(summary_lines))

    for country in ["Россия", "США", "ВОЗ"]:
        for rec in grouped[country]:
            await send_pdf_from_db(rec["rec_id"], update, context)
            await asyncio.sleep(2)


def main():
    app = Application.builder().token("7743250703:AAFxxZq2ugNAK2Uf3WdPH1ngvFJ2lZKk3_M").build()
    app.add_handler(CommandHandler("mkb", handle_mkb))
    print(" Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()