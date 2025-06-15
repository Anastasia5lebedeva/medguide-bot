def format_guideline_for_bot(item: dict) -> str:
    lines = []

    title = item.get("title", "Без названия")
    lines.append(title)

    country = item.get("country")
    if country:
        lines.append(f"Страна: {country}")

    mkb = item.get("mkb_codes", [])
    if mkb:
        lines.append(f"Код МКБ: {mkb[0]}")

    year = item.get("year")
    if isinstance(year, int):
        lines.append(f"Год: {year}")

    summary = item.get("summary")
    if summary and summary.strip():
        lines.append("")
        lines.append("Краткое описание:")
        lines.append(summary.strip())

    diagnostics = item.get("diagnostics", [])
    if diagnostics:
        lines.append("")
        lines.append("Диагностика:")
        lines.extend(f"- {d}" for d in diagnostics)

    treatment = item.get("treatment", [])
    if treatment:
        lines.append("")
        lines.append("Лечение:")
        lines.extend(f"- {t}" for t in treatment)

    return "\n".join(lines)
