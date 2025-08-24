# booking/templatetags/time_extras.py
from django import template
from datetime import time, datetime

register = template.Library()

@register.filter
def format_time(value, fmt="%H:%M"):
    """
    Форматирует time или datetime в 24h HH:MM.
    Если value None — возвращает пустую строку.
    """
    if value is None:
        return ""
    try:
        # если это time или datetime
        if isinstance(value, (time, datetime)):
            return value.strftime(fmt)
        # если передали date/time в виде строки — попытка парсинга не делаем, просто возвращаем как есть
        return str(value)
    except Exception:
        return str(value)

@register.filter
def format_time_range(obj, fmt="%H:%M"):
    """
    Принимает либо объект Availability (с полями start_time/end_time),
    либо кортеж/список (start, end) и возвращает "HH:MM - HH:MM".
    """
    try:
        start = getattr(obj, 'start_time', None)
        end = getattr(obj, 'end_time', None)
        if start and end:
            return f"{start.strftime(fmt)} - {end.strftime(fmt)}"
    except Exception:
        pass
    try:
        if isinstance(obj, (list, tuple)) and len(obj) >= 2:
            s, e = obj[0], obj[1]
            if hasattr(s, 'strftime') and hasattr(e, 'strftime'):
                return f"{s.strftime(fmt)} - {e.strftime(fmt)}"
            return f"{s} - {e}"
    except Exception:
        pass
    return ""
