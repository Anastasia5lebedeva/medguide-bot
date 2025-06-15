import sqlite3
from pathlib import Path

DB_PATH = '/home/anastasia/project.db'

def load_pdfs_into_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, pdf_path FROM recommendations WHERE pdf_path IS NOT NULL")
    rows = cursor.fetchall()

    for rec_id, path in rows:
        full_path = Path(path)
        if not full_path.exists():
            print(f" Файл не найден: {path}")
            continue

        with open(full_path, 'rb') as f:
            blob_data = f.read()
            cursor.execute("UPDATE recommendations SET pdf_blob = ? WHERE id = ?", (blob_data, rec_id))
            print(f" PDF для ID {rec_id}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    load_pdfs_into_db()
