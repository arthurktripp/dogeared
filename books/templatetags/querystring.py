from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def next_page_url(context):
    request = context["request"]
    params = request.GET.copy()

    try:
        page = int(params.get("page", 1))
    except ValueError:
        page = 1

    params["page"] = page + 1
    return f"{request.path}?{params.urlencode()}"


@register.simple_tag(takes_context=True)
def prev_page_url(context):
    request = context["request"]
    params = request.GET.copy()

    try:
        page = int(params.get("page", 1))
    except ValueError:
        page = 1

    params["page"] = page - 1
    return f"{request.path}?{params.urlencode()}"
