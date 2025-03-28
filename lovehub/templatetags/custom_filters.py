from django import template

register = template.Library()

@register.filter(name='abs')
def absolute_value(value):
    """Return the absolute value of a number."""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return value

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get an item from a dictionary using bracket notation in Django template."""
    return dictionary.get(key, None)

@register.filter(name='split')
def split_string(value, delimiter):
    """Split a string by delimiter."""
    return value.split(delimiter) if value else [] 