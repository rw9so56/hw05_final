from django.core.paginator import Paginator

POST_ON_PAGE = 10


def page_paginator(request, objects):
    paginator = Paginator(objects, POST_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
