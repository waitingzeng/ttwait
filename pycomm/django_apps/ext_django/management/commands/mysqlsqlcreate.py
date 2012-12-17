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
from pycomm.django_apps.ext_django.mysqlcreation import sql_create


class Command(AppCommand):
    option_list = AppCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to alter. '
                'Defaults to the "default" database.'),
        make_option('--model', action='store', dest='model',
            default='', help='Nominates a model to alter. '
                'Defaults to the all model'),
    )
    help = "show mysql createa table"

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.indexs = {}


    def handle_app(self, app, **options):

        db = options.get('database', DEFAULT_DB_ALIAS)
        target_model = options.get('model', '').lower()
        style = no_style()
        connection = connections[db]

        output = sql_create(app, target_model, style, connection)
        print '\n'.join(output)
