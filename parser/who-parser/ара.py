import os

# Путь к папке с PDF-документами WHO
pdf_folder = "/home/anastasia/PycharmProjects/medguides/parser/who-parser/who_pdfs"

# Поиск всех PDF-файлов, включая подпапки
pdf_files = []
for root, _, files in os.walk(pdf_folder):
    for file in files:
        if file.lower().endswith(".pdf"):
            pdf_files.append(os.path.join(root, file))

# Вывод найденных файлов
if pdf_files:
    print(f"🔍 Найдено {len(pdf_files)} PDF-файлов:")
    for path in pdf_files:
        print(path)
else:
    print("⚠️ PDF-файлы не найдены в указанной папке.")
