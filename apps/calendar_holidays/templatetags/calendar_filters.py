"""
Custom template filters for calendar_holidays app
"""
from django import template

register = template.Library()


@register.filter(name='dict_lookup')
def dict_lookup(value, arg):
    """
    Looks up an item in a dictionary.
    Usage: {{ my_dict|dict_lookup:key }}
    """
    if isinstance(value, dict):
        return value.get(arg)
    return None


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Alternative dict lookup filter.
    Usage: {{ my_dict|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
