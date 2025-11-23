from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter
def get_previous_month(month, year):
    if month == 1:
        return f'month=12&year={year - 1}'
    return f'month={month - 1}&year={year}'

@register.filter
def get_next_month(month, year):
    if month == 12:
        return f'month=1&year={year+1}'
    return f'month={month+1}&year={year}'
