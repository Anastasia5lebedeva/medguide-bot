import json
import pandas as pd

# 1. Загрузка таблицы соответствия из Excel
mapping_df = pd.read_excel('/home/anastasia/PycharmProjects/medguides/parser/ru-parser/mapped_icd10_to_icd11.xlsx')

# Создаём словарь соответствий: {icd10_code: [icd11_codes]}
mapping_dict = {}
for icd10 in mapping_df['icd10Code'].unique():
    icd11_codes = mapping_df[mapping_df['icd10Code'] == icd10]['icd11Code'].tolist()
    mapping_dict[icd10] = icd11_codes

# 2. Загрузка JSON с клиническими рекомендациями
with open('russian_guidelines.json', 'r', encoding='utf-8') as file:
    guidelines = json.load(file)

# 3. Обработка каждой записи в JSON
missing_codes = set()  # Для логирования кодов без соответствия
for record in guidelines:
    mkb10_codes = record['mkb_codes']
    mkb11_codes = []

    # Для каждого кода МКБ-10 ищем соответствие
    for mkb10 in mkb10_codes:
        if mkb10 in mapping_dict:
            mkb11_codes.extend(mapping_dict[mkb10])
        else:
            missing_codes.add(mkb10)

    # Удаляем дубликаты кодов МКБ-11
    mkb11_codes = list(set(mkb11_codes))

    # Добавляем поле mkb11_codes
    record['mkb11_codes'] = mkb11_codes

# 4. Сохранение обновлённого JSON
with open('russian_guidelines_updated.json', 'w', encoding='utf-8') as file:
    json.dump(guidelines, file, ensure_ascii=False, indent=4)

# 5. Вывод кодов МКБ-10 без соответствия (если есть)
if missing_codes:
    print("Коды МКБ-10, для которых не найдено соответствие МКБ-11:")
    print(sorted(missing_codes))
else:
    print("Все коды МКБ-10 имеют соответствие МКБ-11.")

print("Обновлённый JSON сохранён в 'russian_guidelines_updated.json'")