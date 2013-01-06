from django.contrib.admin.templatetags.admin_list import result_headers, register
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.util import (lookup_field, display_for_field,
    display_for_value)
from django.db import models
from django.utils.encoding import force_text
import datetime
from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
from django.utils.html import format_html
from django.utils.safestring import mark_safe



def items_for_result(cl, result):
    """
    Generates the actual list of data.
    """
    for field_name in cl.list_display:
        row_class = ''
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except ObjectDoesNotExist:
            result_repr = EMPTY_CHANGELIST_VALUE
        else:
            if f is None:
                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                if boolean:
                    allow_tags = True
                result_repr = display_for_value(value, boolean)
                # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if allow_tags:
                    result_repr = mark_safe(result_repr)
                if isinstance(value, (datetime.date, datetime.time)):
                    row_class = mark_safe(' class="nowrap"')
            else:
                if isinstance(f.rel, models.ManyToOneRel):
                    field_val = getattr(result, f.name)
                    if field_val is None:
                        result_repr = EMPTY_CHANGELIST_VALUE
                    else:
                        result_repr = field_val
                else:
                    result_repr = display_for_field(value, f)
                if isinstance(f, (models.DateField, models.TimeField, models.ForeignKey)):
                    row_class = mark_safe(' class="nowrap"')
        if force_text(result_repr) == '':
            result_repr = mark_safe('')
        # If list_display_links not defined, add the link tag to the first field
        if str(result_repr).find('__proxy__') != -1:
            result_repr = ''
        if str(result_repr).isdigit() and len(str(result_repr)) > 10 :
            result_repr = '"%s"' % result_repr
        yield format_html('<td{0}>{1}</td>', row_class, result_repr)

def results(cl):
    for res in cl.result_list:
        yield list(items_for_result(cl, res))



@register.inclusion_tag("admin/export_list_results.html")
def export_result_list(cl):
    """
    Displays the headers and data list together
    """
    headers = list(result_headers(cl))
    return {'cl': cl,
            'result_headers': headers,
            'results': list(results(cl))}
