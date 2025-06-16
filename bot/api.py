from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import aiosqlite
import tempfile
import os
import json
import re
import pdfplumber
import logging

DB_PATH = "/app/data/project.db"
app = FastAPI()

os.makedirs("/bot", exist_ok=True)

logging.basicConfig(
    filename="../bot/api_error.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    text = ""
    try:
        with pdfplumber.open(tmp_path) as pdf:
            logging.info(f" PDF открыт: {tmp_path}, страниц: {len(pdf.pages)}")
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                if t:
                    logging.info(f" Текст извлечён со страницы {i+1}, длина: {len(t)}")
                    text += t + "\n"
                else:
                    logging.warning(f" Нет текста на странице {i+1}")
    except Exception as e:
        logging.error(f"❌ Ошибка извлечения текста из PDF: {e}")
    finally:
        os.remove(tmp_path)

    cleaned = re.sub(r'[^\x00-\x7Fа-яА-ЯёЁ0-9.,!?;:\-\(\)\[\]\{\}\s]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    logging.info(f" Итоговая длина текста: {len(cleaned)} символов")
    return cleaned

@app.get("/recommendations/{mkb_code}")
async def get_recommendations(mkb_code: str):
    mkb_code = mkb_code.upper()
    results = []
    logging.info(f"Запрос рекомендаций для МКБ: {mkb_code}")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM recommendations") as cursor:
            async for row in cursor:
                try:
                    codes = json.loads(row["mkb_codes"])
                    if mkb_code in codes:
                        results.append({
                            "rec_id": row["rec_id"],
                            "title": row["title"],
                            "country": row["country"],
                            "text": row["json_content"],
                            "pdf_url": f"/pdf/{row['rec_id']}"
                        })
                except Exception as e:
                    logging.error(f"Ошибка обработки записи {row['rec_id']}: {e}")

    logging.info(f"Найдено {len(results)} рекомендаций для МКБ: {mkb_code}")
    return results


@app.get("/pdf/{rec_id}")
async def download_pdf(rec_id: str):
    logging.info(f"Запрос PDF для rec_id: {rec_id}")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM recommendations WHERE rec_id = ?", (rec_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                logging.error(f"Запись с rec_id={rec_id} не найдена")
                raise HTTPException(404, "PDF не найден")
            if row["pdf_blob"]:
                logging.info(f"PDF найден в BLOB для rec_id={rec_id}, размер: {len(row['pdf_blob'])} байт")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(row["pdf_blob"])
                    tmp_path = tmp.name
                return FileResponse(
                    tmp_path,
                    media_type="application/pdf",
                    filename=f"{rec_id}.pdf"
                )
            if row["pdf_path"] and os.path.exists(row["pdf_path"]):
                logging.info(f"PDF найден по пути: {row['pdf_path']}")
                return FileResponse(
                    row["pdf_path"],
                    media_type="application/pdf",
                    filename=os.path.basename(row["pdf_path"])
                )

            logging.error(f"PDF не найден для rec_id={rec_id}: нет pdf_path или pdf_blob")
            raise HTTPException(404, "PDF не найден")