#!/usr/bin/python
#coding=utf8
import fields
from django.contrib.auth import models as auth_app, get_user_model
from django.core import exceptions
from django.core.management.base import CommandError
from django.db.models import get_models, signals
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.auth.management import _get_permission_codename
from pycomm.django_apps.ext_django import models


def _get_permissions(opts):
    perms = []
    for action in ('view', 'export'):
        perms.append((_get_permission_codename(action, opts),
            'Can %s %s' % (action, opts.verbose_name_raw)))
    return perms

def create_permissions(app, created_models, verbosity, **kwargs):
    from django.contrib.contenttypes.models import ContentType

    app_models = get_models(app)

    # This will hold the permissions we're looking for as
    # (content_type, (codename, name))
    searched_perms = list()
    # The codenames and ctypes that should exist.
    ctypes = set()
    for klass in app_models:
        ctype = ContentType.objects.get_for_model(klass)
        ctypes.add(ctype)
        for perm in _get_permissions(klass._meta):
            searched_perms.append((ctype, perm))

    # Find all the Permissions that have a context_type for a model we're
    # looking for.  We don't need to check for codenames since we already have
    # a list of the ones we're going to create.
    all_perms = set(auth_app.Permission.objects.filter(
        content_type__in=ctypes,
    ).values_list(
        "content_type", "codename"
    ))

    objs = [
        auth_app.Permission(codename=codename, name=name, content_type=ctype)
        for ctype, (codename, name) in searched_perms
        if (ctype.pk, codename) not in all_perms
    ]
    auth_app.Permission.objects.bulk_create(objs)
    if verbosity >= 2:
        for obj in objs:
            print("Adding permission '%s'" % obj)



signals.post_syncdb.connect(create_permissions,
    dispatch_uid="alterdb.create_permissions")



import django.contrib.admin
from django.utils.text import capfirst
from django.utils.datastructures import SortedDict

def find_model_index(name):
    count = 0
    for model, model_admin in django.contrib.admin.site._registry.items():
        if capfirst(model._meta.verbose_name_plural) == name:
            return count
        else:
            count += 1
    return count
       
def index_decorator(func):
    def inner(*args, **kwargs):
        templateresponse = func(*args, **kwargs)
        for app in templateresponse.context_data['app_list']:
            app['models'].sort(key=lambda x: find_model_index(x['name']))
        return templateresponse
    return inner

registry = SortedDict()
registry.update(django.contrib.admin.site._registry)
django.contrib.admin.site._registry = registry
django.contrib.admin.site.index = index_decorator(admin.site.index)
django.contrib.admin.site.app_index = index_decorator(admin.site.app_index)

