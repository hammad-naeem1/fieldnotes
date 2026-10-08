import markdown
import nh3
from django.utils.safestring import mark_safe

ALLOWED_TAGS = {
    "a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3", "h4", "hr", "img",
    "li", "ol", "p", "pre", "span", "div", "strong", "table", "tbody", "td", "th", "thead", "tr", "ul",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title", "width", "height"},
    "code": {"class"},
    "pre": {"class"},
    "span": {"class"},
    "div": {"class"},
    "th": {"align"},
    "td": {"align"},
}


def render_markdown(value):
    html = markdown.markdown(
        value or "",
        extensions=["fenced_code", "tables", "codehilite"],
        output_format="html5",
    )
    safe_html = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
    )
    return mark_safe(safe_html)
