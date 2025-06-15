import fitz  # PyMuPDF


# Функция для извлечения текста из PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text("text")
    return text


# Функция для проверки на клинические рекомендации
def is_clinical_guideline(text):
    # Ищем ключевые слова в тексте
    keywords = ["clinical guideline", "recommendation", "treatment", "management", "diagnosis", "WHO"]
    for kw in keywords:
        if kw.lower() in text.lower():
            return True
    return False


# Пример использования
output_dir = "/home/anastasia/PycharmProjects/medguides/clinical_guidelines"  # Папка, где сохраняются скачанные файлы
downloaded_files = ["PMC2622843.pdf", "WHO-IVB-2023.01-eng.pdf"]  # Скачанные файлы

for file_name in downloaded_files:
    pdf_path = os.path.join(output_dir, file_name)

    # Извлекаем текст из PDF
    text = extract_text_from_pdf(pdf_path)

    # Проверяем, является ли это клинической рекомендацией
    if is_clinical_guideline(text):
        print(f"{file_name} - это клиническая рекомендация.")
    else:
        print(f"{file_name} - это НЕ клиническая рекомендация.")
