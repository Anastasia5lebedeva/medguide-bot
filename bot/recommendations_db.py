import aiosqlite
import json

DB_PATH = "/home/anastasia/project.db"

async def search_recommendations_by_icd(icd_code: str):
    results = []
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM recommendations") as cursor:
            columns = [column[0] for column in cursor.description]
            async for row in cursor:
                rec = dict(zip(columns, row))
                mkb_codes = json.loads(rec["mkb_codes"])
                if any(icd_code.upper() in code.upper() for code in mkb_codes):
                    results.append(rec)
    return results

