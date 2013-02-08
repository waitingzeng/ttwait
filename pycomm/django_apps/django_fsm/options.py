#!/usr/bin/python
#coding=utf8
from django.contrib import admin
from pycomm.django_apps.ext_django.admin import ModelAdmin
from django.contrib.admin.options import InlineModelAdmin
import models
from django.contrib.contenttypes import generic



class FSMMixin(object):
    def get_allow_trans(self, request, obj):
        opts = obj._meta
        allow_trans = []
        for target, tran in obj.get_available_transitions():
            tran_name = tran.__name__
            tran_desc = tran.verbose_name or tran_name
            if request.user.has_perm('%s.%s_%s' % (opts.app_label, tran_name, opts.module_name)):
                allow_trans.append((tran_name, tran_desc))

        return allow_trans

    def has_fsm_permission(self, request, obj=None, model=None):
        if obj is None and model is None:
            return False
        if obj:
            cur_status = obj.get_cur_status()
            opts = obj._meta
            fsm_field = obj.fsm_field
        else:
            cur_status = model.fsm_field.default
            opts = model._meta
            fsm_field = model.fsm_field
        code = '%s.change_%s_%s_%s' % (opts.app_label, cur_status, fsm_field.name, opts.module_name)
        if not request.user.has_perm(code):
            return False
        return True


    def get_all_fields(self, request, obj):
        fieldsets = self.get_fieldsets(request, obj)
        all_fields = []
        for fieldset in fieldsets:
            for fields in fieldset[1]['fields']:
                if isinstance(fields, basestring):
                    fields = [fields]
                for field in fields:
                    all_fields.append(field)
        return all_fields

class FSMInline(FSMMixin, InlineModelAdmin):
    
    def has_add_permission(self, request):
        if not self.has_fsm_permission(request, model=self.parent_model):
            return False
        return super(FSMInline, self).has_add_permission(request)
        


    def get_form(self, request, obj=None):
        if obj:
            cur_status = obj.get_cur_status()
            if hasattr(self, '%s_form' % cur_status):
                return getattr(self, '%s_form' % cur_status)
        return super(FSMInline, self).get_form(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if not self.has_fsm_permission(request, obj):
                return self.get_all_fields(request, obj)

            cur_status = obj.get_cur_status()
            if hasattr(self, '%s_readonly_fields' % cur_status):
                return getattr(self, '%s_readonly_fields' % cur_status)
        return super(FSMInline, self).get_readonly_fields(request, obj)
    

    


    def get_fieldsets(self, request, obj=None):

        if not obj:
            cur_status = self.parent_model.fsm_field.default
        else:
            cur_status = obj.get_cur_status()

        if hasattr(self, '%s_fieldsets' % cur_status):
            return getattr(self, '%s_fieldsets' % cur_status)
        
        if hasattr(self, '%s_fields' % cur_status):
            fields = getattr(self, '%s_fields' % cur_status)
            return [(None, {'fields': self.fields})]

        return super(FSMInline, self).get_fieldsets(request, obj)

    def get_allow_trans(self, request, obj):
        opts = self.model._meta
        allow_trans = []
        for target, tran in obj.get_available_transitions():
            tran_name = tran.__name__
            tran_desc = tran.verbose_name or tran_name
            if request.user.has_perm('%s.%s_%s' % (opts.app_label, tran_name, opts.module_name)):
                allow_trans.append((tran_name, tran_desc))

        return allow_trans


class StackedInline(FSMInline):
    template = 'admin/edit_inline/stacked.html'


class TabularInline(FSMInline):
    template = 'admin/edit_inline/tabular.html'




class ModelStatusChangeInline(generic.GenericTabularInline):
    model = models.ModelStatusChange
    can_delete = False
    extra = 0
    fields = ['user', 'status_from', 'status_to', 'create_time']
    readonly_fields = fields

    classes = ('grp-collapse grp-closed',)
    inline_classes = ('grp-collapse grp-closed',)


    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return False



class FSMAdmin(FSMMixin, ModelAdmin):
    inlines = [ModelStatusChangeInline]
    def get_form(self, request, obj=None):
        if obj:
            cur_status = obj.get_cur_status()
            if hasattr(self, '%s_form' % cur_status):
                return getattr(self, '%s_form' % cur_status)
        return super(FSMAdmin, self).get_form(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if not self.has_fsm_permission(request, obj):
                return self.get_all_fields(request, obj)
            cur_status = obj.get_cur_status()
            if hasattr(self, '%s_readonly_fields' % cur_status):
                return getattr(self, '%s_readonly_fields' % cur_status)
        return super(FSMAdmin, self).get_readonly_fields(request, obj)
    

    def get_fieldsets(self, request, obj=None):

        if not obj:
            cur_status = self.model.fsm_field.default
        else:
            cur_status = obj.get_cur_status()

        if hasattr(self, '%s_fieldsets' % cur_status):
            return getattr(self, '%s_fieldsets' % cur_status)
        
        if hasattr(self, '%s_fields' % cur_status):
            fields = getattr(self, '%s_fields' % cur_status)
            return [(None, {'fields': self.fields})]

        return super(FSMAdmin, self).get_fieldsets(request, obj)


    def response_change(self, request, obj, *args, **kwargs):
        
        allow_trans = self.get_allow_trans(request, obj)
        for name, tran in allow_trans:
            if "_%s" % name in request.POST:
                getattr(obj, name)(request=request)

            request.POST['_continue'] = True

        return super(FSMAdmin, self).response_change(request, obj, *args, **kwargs)



