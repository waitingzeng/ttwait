#! /usr/bin/env python
#coding=utf-8
from optparse import make_option
from django.core.management.base import NoArgsCommand, AppCommand
from django.core.management.color import no_style
from django.db import connections, router, models, DEFAULT_DB_ALIAS
import copy
from django.core.management.base import CommandError
from django.db.backends.mysql.creation import DatabaseCreation
from django.db.models.fields import NOT_PROVIDED
from pycomm.django_apps.ext_django.admin import auto_admin_for_models


class Command(AppCommand):
    def get_def_from_admin(self, admin):
        outputs = []
        outputs.append("class %s(admin.ModelAdmin):" % admin.__name__)
        outputs.append("    list_per_page = %s" % admin.list_per_page)
        outputs.append("    list_select_related = %s" % admin.list_select_related)
        outputs.append("    list_display = %s" % admin.list_display)
        outputs.append("    search_fields = %s" % admin.search_fields)
        outputs.append("    list_filter = %s" % admin.list_filter)
        outputs.append("    list_editable = %s" % admin.list_editable)
        outputs.append("    date_hierarchy = %s" % admin.date_hierarchy)

        outputs.append("")
        outputs.append("admin.site.register(%s, %s)" % (admin.__name__[:-5], admin.__name__))
        return '\n'.join(outputs)

    def handle_app(self, app, **options):

        admins = auto_admin_for_models(app)
        outputs = []
        for admin in admins:
            outputs.append(self.get_def_from_admin(admin))

        print '\n\n'.join(outputs)
            
