# booking/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dict_obj, key):
    """
    Возвращает dict_obj[key] или None. Используйте в шаблоне:
    {{ day_counts|get_item:day }}
    """
    try:
        return dict_obj.get(key)
    except Exception:
        try:
            # попробовать привести ключ к строке
            return dict_obj.get(str(key))
        except Exception:
            return None
