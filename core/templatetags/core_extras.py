from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def pesos_cl(value):
    """Formatea un número como peso chileno: 100000 → 100.000"""
    if value is None or value == '':
        return '0'
    try:
        return f'{int(value):,}'.replace(',', '.')
    except (ValueError, TypeError):
        return str(value)
