# coding: utf-8
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate(queryset, number, per_page, reverse=False):
    paginator = Paginator(queryset, per_page)

    try:
        page = paginator.page(number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page = paginator.page(paginator.num_pages)

    paginator.page_ranges = get_page_ranges(page.number, paginator.num_pages)
    if reverse:
        paginator.page_ranges.reverse()
        for r in paginator.page_ranges:
            r.reverse()
    page.page_ranges = paginator.page_ranges
    return page


def get_page_ranges(number, num_pages):
    if num_pages <= 4:
        return [range(1, num_pages + 1)]
    elif number < (num_pages - 1):
        if number == 1:
            return [[number, number + 1], [num_pages]]
        return [[1], [number, number + 1], [num_pages]]
    else:
        return [[1], [num_pages - 1, num_pages]]
    
