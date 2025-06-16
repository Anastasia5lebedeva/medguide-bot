import os

# Папка с PDF
folder_path = '/home/anastasia/PycharmProjects/medguides/parser/who-parser/clinical_guidelines_WHO'

# Путь к списку файлов на удаление
delete_list_path = '/home/anastasia/PycharmProjects/medguides/translated_filenames.csv'

# Функция очистки имени
def clean_filename(name):
    # Убираем кавычки, запятые, пробелы в начале и конце
    return name.replace('"', '').replace("'", '').replace(',', '').strip().lower()

# Читаем список для удаления
with open(delete_list_path, encoding='utf-8') as f:
    delete_files = [clean_filename(line) for line in f if clean_filename(line)]

# Получаем имена всех файлов в папке
folder_files = os.listdir(folder_path)

deleted = 0
not_found = []

for target_name in delete_files:
    found = False
    for real_file in folder_files:
        clean_real = clean_filename(real_file)
        # Совпадение по "концу имени"
        if clean_real.endswith(target_name):
            full_path = os.path.join(folder_path, real_file)
            os.remove(full_path)
            print(f'Удалено: {real_file}')
            deleted += 1
            found = True
            break
    if not found:
        print(f'Не найден: {target_name}')
        not_found.append(target_name)

print(f'\nГотово! Удалено файлов: {deleted}')
if not_found:
    print("\nФайлы, которые не удалось найти:")
    for nf in not_found:
        print(nf)
