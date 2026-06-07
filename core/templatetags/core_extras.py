from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permite acceder a un dict con variable como clave: dict|get_item:variable"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
