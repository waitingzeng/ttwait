from optparse import make_option
import traceback

from django.conf import settings
from django.core.management import call_command
from django.core.management.commands.syncdb import Command as SyncDBCommend
from django.core.management.color import no_style
from django.core.management.sql import custom_sql_for_model, emit_post_sync_signal
from django.db import connections, router, transaction, models, DEFAULT_DB_ALIAS
from django.utils.datastructures import SortedDict
from django.utils.importlib import import_module
from pycomm.django_apps.ext_django.mysqlcreation import MysqlCreation


class Command(SyncDBCommend):
    def handle_noargs(self, **options):

        db = options.get('database')
        connection = connections[db]
        connection.creation = MysqlCreation(connection)
        return SyncDBCommend.handle_noargs(self, **options)

