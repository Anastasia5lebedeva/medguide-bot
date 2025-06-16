import os
import pdfplumber
from deep_translator import GoogleTranslator

# Путь к папке с PDF
folder = "/home/anastasia/PycharmProjects/medguides/parser/who-parser/clinical_guidelines_WHO"

# Список всех PDF-файлов
pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]

# Переводчик
translator = GoogleTranslator(source='auto', target='ru')

for filename in pdf_files:
    file_path = os.path.join(folder, filename)

    # Перевод названия файла
    name_only = os.path.splitext(filename)[0]
    translated_name = translator.translate(name_only)
    print(f"📄 Название: {filename} → 🪄 {translated_name}")

    # Попытка прочитать текст из PDF
    try:
        with pdfplumber.open(file_path) as pdf:
            all_text = ""
            for page in pdf.pages[:3]:  # Ограничимся 3 страницами, чтобы не тормозило
                all_text += page.extract_text() or ""
            if all_text.strip():
                translated_text = translator.translate(all_text[:1000])  # Переведём первые 1000 символов
                print(f"📝 Перевод текста (начало):\n{translated_text}\n")
            else:
                print("⚠️ Текст не найден (возможно, это скан).")
    except Exception as e:
        print(f"❌ Ошибка при чтении {filename}: {e}")

    print("─" * 60)
