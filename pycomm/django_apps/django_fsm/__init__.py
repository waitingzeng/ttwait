# -*- coding: utf-8 -*-
"""
State tracking functionality for django models
"""
from django.db.models import get_models, signals
from django.contrib.auth.management import _get_permission_codename
from pycomm.django_apps.django_fsm.db.fields import FSMField

def all_fsm_fields(opts):
    return [field for field in opts.fields \
            if isinstance(field, FSMField)]

def _get_permissions(opts):    
    fields = all_fsm_fields(opts)
    perms = []
    for field in fields:
        sources, any_targets = [], []

        for transition in field.transitions:  
            action = transition.__name__
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
