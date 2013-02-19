#!/usr/bin/python
#coding=utf8

from django import template

register = template.Library()

def has_fsm_permission(request, obj):
    cur_status = obj.get_cur_status()
    opts = obj._meta
    code = '%s.change_%s_%s_%s' % (opts.app_label, cur_status, obj.fsm_field.name, opts.module_name)
    if not request.user.has_perm(code):
        return False
    return True



@register.inclusion_tag('admin/fsm_submit_line.html', takes_context=True)
def fsm_submit_row(context):
    """
    Displays the row of buttons for delete and save.
    """

    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    request = context['request']
    save_as = context['save_as']
    obj = context.get('original', None)
    ctx = {
        'opts': opts,
        'onclick_attrib': (opts.get_ordered_objects() and change
                            and 'onclick="submitOrderForm();"' or ''),
        'show_delete_link': (not is_popup and context['has_delete_permission']
                              and change and context.get('show_delete', True)),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and
                            not is_popup and (not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'original' : obj,
        'show_return' : False,
    }

    allow_trans = []
    if obj:
        for target, tran in obj.get_available_transitions():
            tran_name = tran.__name__
            tran_desc = tran.verbose_name or tran_name
            if request.user.has_perm('%s.%s_%s' % (opts.app_label, tran_name, opts.module_name)):
                allow_trans.append((tran_name, tran_desc))

    ctx['transitions'] = allow_trans
    if allow_trans:
        ctx.update({
            'show_save' : False,
            'show_save_as_new': False,
            'show_save_and_add_another': False,
        })

    if obj and not has_fsm_permission(request, obj):
        ctx.update({
            'show_delete_link' : False,
            'show_save' : False,
            'show_save_as_new' : False,
            'show_save_and_continue' : False,
            'show_save_and_add_another' : False,
            'show_return' : True,
        })
    return ctx
