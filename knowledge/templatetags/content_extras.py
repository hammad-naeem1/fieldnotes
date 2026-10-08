from django import template

from knowledge.rendering import render_markdown

register = template.Library()


@register.filter
def markdown_content(value):
    return render_markdown(value)
