from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import json
import os

app = FastAPI()

JSON_DATA = "/home/anastasia/PycharmProjects/medguides/parser/ru_guidelines.json"


@app.get("/search/{mkb_code}")
async def search_by_mkb_code(mkb_code: str):

    if not os.path.exists(JSON_DATA):
        raise HTTPException(status_code=500, detail="Файл данных не найден")
    with open(JSON_DATA, "r", encoding="utf-8") as f:
        data = json.load(f)

    mkb_code = mkb_code.upper()
    for item in data:
        if mkb_code in item["mkb_codes"]:
            pdf_path = item.get("pdf_path")
            if pdf_path and os.path.exists(pdf_path):
                return FileResponse(pdf_path, media_type="application/pdf", filename=f"{item['rec_id']}.pdf")
            raise HTTPException(status_code=404, detail="PDF не найден")
    raise HTTPException(status_code=404, detail="Рекомендация не найдена")