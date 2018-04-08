from django import template

register = template.Library()


@register.filter(filename="home.html", name = 'get_item')
def get_item(dictionary, key):
    return dictionary.get(key)
