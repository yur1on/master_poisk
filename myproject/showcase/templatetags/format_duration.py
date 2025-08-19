from django import template
import re

register = template.Library()


@register.filter
def format_duration(value):
    if not value:
        return "Не указано"

    # Если значение уже в формате "X ч Y мин" или "X ч" или "Y мин", возвращаем без изменений
    if re.match(r'^\d+\s*ч(\s*\d+\s*мин)?$', value, re.IGNORECASE) or re.match(r'^\d+\s*мин$', value, re.IGNORECASE):
        return value

    # Пытаемся извлечь число и единицу измерения
    try:
        # Извлекаем число и единицу (например, "1.5 часа" → 1.5, "часа"; "90 мин" → 90, "мин")
        match = re.match(r'(\d+(\.\d+)?)\s*(часа|час|ч|мин|минут|м)?', value, re.IGNORECASE)
        if match:
            number = float(match.group(1))
            unit = match.group(3).lower() if match.group(3) else None

            if unit in ['час', 'часа', 'ч']:
                # Конвертируем часы в часы и минуты
                hours = int(number)
                minutes = int((number - hours) * 60)
                if hours > 0 and minutes > 0:
                    return f"{hours} ч {minutes} мин"
                elif hours > 0:
                    return f"{hours} ч"
                else:
                    return f"{minutes} мин"
            elif unit in ['мин', 'минут', 'м'] or unit is None:
                # Конвертируем минуты в часы и минуты
                hours = int(number // 60)
                minutes = int(number % 60)
                if hours > 0 and minutes > 0:
                    return f"{hours} ч {minutes} мин"
                elif hours > 0:
                    return f"{hours} ч"
                else:
                    return f"{int(number)} мин"
    except (ValueError, TypeError):
        pass

    # Если формат не распознан, возвращаем исходное значение
    return value or "Не указано"