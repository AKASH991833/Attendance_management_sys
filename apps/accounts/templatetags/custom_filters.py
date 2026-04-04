"""
Custom template filters for EduTrack Pro
"""
from django import template

register = template.Library()


@register.filter(name='dict_lookup')
def dict_lookup(value, arg):
    """
    Allows dictionary lookup in templates.
    Usage: {{ my_dict|dict_lookup:key }}
    """
    if isinstance(value, dict):
        return value.get(arg, [])
    return []
