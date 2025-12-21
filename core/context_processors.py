from django.utils.safestring import mark_safe

def brand(request):
    return {
        "brand": mark_safe("<em>dog&#8209;eared</em>"),
    }