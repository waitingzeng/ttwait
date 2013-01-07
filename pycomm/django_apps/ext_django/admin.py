#!/usr/bin/python
#coding=utf8
from django.contrib import admin
from django.db import models
from django.conf.urls import patterns, url
from changelist import ExportChangeList, QuerySetChangeList
from django.core.exceptions import PermissionDenied
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.http import HttpResponse
from django.contrib.admin.options import csrf_protect_m, update_wrapper
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from pycomm.utils.pprint import pformat
from pycomm.log import log, PrefixLog
from django.contrib.admin.views.main import ALL_VAR
from actions import csv_export_selected


class ModelAdmin(admin.ModelAdmin):
    list_export_fields = None
    stat_list_filter = None

    class Media:
        css = { "all" : ("css/custom.css",) }
        js = ("js/custom.js",) 

    def __init__(self, *args, **kwargs):
        admin.ModelAdmin.__init__(self, *args, **kwargs)
        info = self.model._meta.app_label, self.model._meta.module_name
        self.log = PrefixLog('admin:%s_%s' % info)

    def has_view_permission(self, request, obj=None):
        opts = self.opts
        view_permission = 'view_%s' %self.model._meta.module_name
        return request.user.has_perm(opts.app_label + '.' + view_permission)

    def has_export_permission(self, request, obj=None):
        opts = self.opts
        export_permission = 'export_%s' % opts.module_name
        return request.user.has_perm(opts.app_label + '.' + export_permission)

    def has_stat_permission(self, request, obj=None):
        opts = self.opts
        stat_permission = 'stat_%s' % opts.module_name
        return request.user.has_perm(opts.app_label + '.' + stat_permission)


    def has_change_permission(self, request, obj=None):
        if hasattr(self,'has_change'):
          if self.has_change:
              return True

        return admin.ModelAdmin.has_change_permission(self, request, obj)

    def get_model_perms(self, request):
        value = admin.ModelAdmin.get_model_perms(self, request)
        value['view'] = self.has_view_permission(request)
        value['export'] = self.has_export_permission(request)
        value['stat'] = self.has_stat_permission(request)
        return value        

    def log_change(self, request, object, message):
        admin.ModelAdmin.log_change(self, request, object, message)

        self.log.trace('user %s change %s %s', request.user, object, message)

    def construct_change_message(self, request, form, formsets):
        """
        Construct a change message from a changed object.
        """
        change_message = []
        if form.changed_data:
            change_message.append(_('Changed %s.') % pformat(form.changed_data))

        if formsets:
            for formset in formsets:
                for added_object in formset.new_objects:
                    change_message.append(_('Added %(name)s "%(object)s".')
                                          % {'name': force_text(added_object._meta.verbose_name),
                                             'object': force_text(added_object)})
                for changed_object, changed_fields in formset.changed_objects:
                    change_message.append(_('Changed %(list)s for %(name)s "%(object)s".')
                                          % {'list': pformat(changed_fields),
                                             'name': force_text(changed_object._meta.verbose_name),
                                             'object': force_text(changed_object)})
                for deleted_object in formset.deleted_objects:
                    change_message.append(_('Deleted %(name)s "%(object)s".')
                                          % {'name': force_text(deleted_object._meta.verbose_name),
                                             'object': force_text(deleted_object)})
        change_message = ' '.join(change_message)
        return change_message or _('No fields changed.')

    def get_custom_urls(self, info):
        return None

    def wrap(self, view):
        def wrapper(*args, **kwargs):
            return self.admin_site.admin_view(view)(*args, **kwargs)
        return update_wrapper(wrapper, view)

    def get_urls(self):

        info = self.model._meta.app_label, self.model._meta.module_name
        export_url = patterns('',
            url(r'^stat/$',
                self.wrap(self.stat_view),
                name='%s_%s_stat' % info),
        )

        urlpatterns = self.get_custom_urls(info)
        print urlpatterns
        if not urlpatterns:
            return  export_url + admin.ModelAdmin.get_urls(self)
        else:
            return export_url + urlpatterns + admin.ModelAdmin.get_urls(self)

        return urlpatterns

    def get_hasperm_url(self, request, obj):
        from django.core.urlresolvers import reverse

        opts = obj._meta
        app_label = opts.app_label
        model_name = opts.module_name
        site_name = self.admin_site.name

        hasperm_url = 'admin:%s_%s_changelist' % (app_label, model_name)
        url = reverse(hasperm_url, current_app=site_name)
        return url

    def get_extra_info(self, request):
        extra_info = request.GET.get('extra_info')
        if not extra_info:
            return None
        extra_info = extra_info.split('|', 1)
        return extra_info

    def get_export_fields(self, request):
        fields = [(x.name, x.verbose_name) for x in self.opts.fields]
        
        if not self.list_export_fields:
            return fields

        dict_fields = dict(fields)
        fields = []
        for field in self.list_export_fields:
            if field in dict_fields:
                fields.append([field, dict_fields[field]])
            else:
                func = getattr(self, field, None)
                if not func or not callable(func):
                    raise Exception("Not Found Field %s in %s" % (field, self.__class__.__name__))
                fields.append((field, func.__name__))
        return fields

    def export_model(self, model, queryset, list_display, model_admin=None):
        opts = model._meta
        app_label = opts.app_label
        cl = QuerySetChangeList(model, queryset, list_display, model_admin=model_admin)
        
        context = {
            'cl' : cl,
        }

        response = SimpleTemplateResponse([
            "admin/%s/%s/export_model.html" % (app_label, opts.object_name.lower()),
            "admin/%s/export_model.html" % app_label,
            "admin/export_model.html"], context)
        response.render()
        return response.content

    
    def get_chartit(self, request, cl):
        raise NotImplementedError

    def stat_view(self, request):
        if not self.has_stat_permission(request):
            raise PermissionDenied
        opts = self.model._meta
        app_label = opts.app_label

        request.GET = dict(request.GET.items())

        list_display = self.get_list_display(request)
        list_filter = self.stat_list_filter and self.list_filter + self.stat_list_filter or self.list_filter
        cl = ExportChangeList(self, request, self.model, list_display, list_filter)
        
        stat_chartit = self.get_chartit(request, cl)
        context = {
                'app_label': app_label,
                'media': self.media,
                'stat_chartit' : stat_chartit,
                'cl' : cl,
                'opts' : opts,
            }
        res = TemplateResponse(request, [
        "admin/%s/%s/stat_result.html" % (app_label, opts.object_name.lower()),
        'admin/%s/stat_result.html' % app_label,
        "admin/stat_result.html"], context, current_app=self.admin_site.name)
        self.add_response_media(res)
        return res

    def add_response_media(self, response):
        cl = response.context_data.get('cl', None)
        if cl:
            media = response.context_data['media']
            if cl.has_filters:
                for spec in cl.filter_specs:
                    if not hasattr(spec, 'form'):
                        continue

                    media = media + spec.form.media
                response.context_data['media'] = media

    def before_changelist_view(self, request, extra_context):
        pass

    def after_changelist_view(self, request, response):
        pass


    def changelist_view(self, request, extra_context=None):
        if self.has_view_permission(request, None):
            self.has_change = True
        
        if not extra_context:
            extra_context = {}

        ret = self.before_changelist_view(request, extra_context)
        if isinstance(ret, HttpResponse):
            return ret

        response = admin.ModelAdmin.changelist_view(self, request, extra_context)
        try:
            response.context_data['has_export_permission'] = self.has_export_permission(request)
            response.context_data['has_stat_permission'] = self.has_stat_permission(request)
            path = request.get_full_path().split('?')
            if len(path) == 2:
                params = '?' + path[1]
            else:
                params = ''
            response.context_data['querystring'] = params
            self.add_response_media(response)
            
        except:
            pass

        self.has_change = False

        ret = self.after_changelist_view(request, response)
        if isinstance(ret, HttpResponse):
            return ret

        return response                

    def before_change_view(self, request, object_id, form_url, extra_context):
        pass

    def after_change_view(self, request, response):
        pass

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}

        ret = self.before_change_view(request, object_id, form_url, extra_context)
        if isinstance(ret, HttpResponse):
            return ret

        response = admin.ModelAdmin.change_view(self, request, object_id, form_url, extra_context)

        ret = self.after_change_view(request, response)
        if isinstance(ret, HttpResponse):
            return ret
        return response


    def get_actions(self, request):
        actions = super(ModelAdmin, self).get_actions(request)
        if self.has_export_permission(request):
            actions[csv_export_selected.__name__] = (csv_export_selected, csv_export_selected.__name__, csv_export_selected.short_description)
        return actions

site = admin.site
TabularInline = admin.TabularInline
StackedInline = admin.StackedInline
VERTICAL = admin.VERTICAL

def create_admin_models(model):
    opt = model._meta
    fields = opt.local_fields
    class AutoModelAdmin(ModelAdmin):
        list_per_page = 20
        list_select_related = False
        pass
    AutoModelAdmin.__name__ = '%sAdmin' % model.__name__

    AutoModelAdmin.list_display = [x.name for x in fields if x.editable and not isinstance(x, models.ForeignKey)]
    AutoModelAdmin.search_fields = getattr(model, 'search_fields', []) or \
        [x.name for x in fields if isinstance(x, (models.CharField, models.TextField))]

    AutoModelAdmin.list_filter = getattr(model, 'list_filter', []) or \
        [x.name for x in fields if x.choices or isinstance(x, models.DateTimeField)]
    AutoModelAdmin.list_editable = [x for x in  AutoModelAdmin.list_filter if x in AutoModelAdmin.list_display]

    #datetime_fields = [x.name for x in fields if isinstance(x, models.DateTimeField)]
    #if datetime_fields:
    #    AutoModelAdmin.date_hierarchy = getattr(model, 'date_hierarchy', None) or datetime_fields[0]
    return AutoModelAdmin

def auto_admin_for_models(app_models, app_labels=None, register=True):
    admins = []
    for name in dir(app_models):
        model = getattr(app_models, name)
    
        if getattr(model, 'noadmin', False):
            continue
        
        if isinstance(model, type) and issubclass(model, models.Model) and model not in admin.site._registry:
            opt = model._meta

            if opt.abstract:
                continue

            if app_labels and opt.app_label not in app_labels:
                continue


            model_admin = create_admin_models(model)

            if register:
                admin.site.register(model, model_admin)
            admins.append(model_admin)
    return admins


