from __future__ import unicode_literals

import keyword
import re
from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django.utils import six
from django.core.management.commands.inspectdb import Command as InspectDBCommand

class Command(InspectDBCommand):

    requires_model_validation = False

    def handle_inspection(self, options):
        connection = connections[options.get('database')]
        # 'table_name_filter' is a stealth option
        table_name_filter = options.get('table_name_filter')

        table2model = lambda table_name: table_name.title().replace('_', '').replace(' ', '').replace('-', '')
        strip_prefix = lambda s: s.startswith("u'") and s[1:] or s

        cursor = connection.cursor()
        yield "# This is an auto-generated Django model module."
        yield "# You'll have to do the following manually to clean this up:"
        yield "#     * Rearrange models' order"
        yield "#     * Make sure each model has one field with primary_key=True"
        yield "# Feel free to rename the models, but don't rename db_table values or field names."
        yield "#"
        yield "# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'"
        yield "# into your database."
        yield "from __future__ import unicode_literals"
        yield ''
        yield 'from %s import models' % self.db_module
        yield ''
        known_models = []
        for table_name in connection.introspection.table_names(cursor):
            if table_name_filter is not None and callable(table_name_filter):
                if not table_name_filter(table_name):
                    continue
            yield 'class %s(models.Model):' % table2model(table_name)
            known_models.append(table2model(table_name))
            try:
                relations = connection.introspection.get_relations(cursor, table_name)
            except NotImplementedError:
                relations = {}
            try:
                indexes = connection.introspection.get_indexes(cursor, table_name)
            except NotImplementedError:
                indexes = {}
            used_column_names = [] # Holds column names used in the table so far
            for i, row in enumerate(self.get_table_description(connection, cursor, table_name)):
                comment_notes = [] # Holds Field notes, to be displayed in a Python comment.
                extra_params = {}  # Holds Field parameters such as 'db_column'.
                column_name = row[0]
                is_relation = i in relations

                att_name, params, notes = self.normalize_col_name(
                    column_name, used_column_names, is_relation)
                extra_params.update(params)
                comment_notes.extend(notes)

                used_column_names.append(att_name)

                # Add primary_key and unique, if necessary.
                if column_name in indexes:
                    if indexes[column_name]['primary_key']:
                        extra_params['primary_key'] = True
                    elif indexes[column_name]['unique']:
                        extra_params['unique'] = True

                if is_relation:
                    rel_to = relations[i][1] == table_name and "'self'" or table2model(relations[i][1])
                    if rel_to in known_models:
                        field_type = 'ForeignKey(%s' % rel_to
                    else:
                        field_type = "ForeignKey('%s'" % rel_to
                else:
                    # Calling `get_field_type` to get the field type string and any
                    # additional paramters and notes.
                    field_type, field_params, field_notes = self.get_field_type(connection, table_name, row)
                    extra_params.update(field_params)
                    comment_notes.extend(field_notes)

                    field_type += '('

                # Don't output 'id = meta.AutoField(primary_key=True)', because
                # that's assumed if it doesn't exist.
                if att_name == 'id' and field_type == 'AutoField(' and extra_params == {'primary_key': True}:
                    continue

                extra_params['db_column'] = column_name

                # Add 'null' and 'blank', if the 'null_ok' flag was present in the
                # table description.
                if row[6]: # If it's NULL...
                    extra_params['blank'] = True
                    if not field_type in ('TextField(', 'CharField('):
                        extra_params['null'] = True
                
                if row[8] is not None:
                    extra_params['default'] = row[8]

                field_desc = '%s = models.%s' % (att_name, field_type)
                if extra_params:
                    if not field_desc.endswith('('):
                        field_desc += ', '
                    field_desc += ', '.join([
                        '%s=%s' % (k, strip_prefix(repr(v)))
                        for k, v in extra_params.items()])
                if row[7]:
                    if not field_desc.endswith('('):
                        field_desc += ', '
                    field_desc += 'verbose_name="' +  row[7].encode('utf-8') + '"'
                    field_desc += ', help_text="' +  row[7].encode('utf-8') + '"'
                field_desc += ')'
                if comment_notes:
                    field_desc += ' # ' + ' '.join(comment_notes)
                yield '    %s' % field_desc
            for meta_line in self.get_meta(table_name):
                yield meta_line


    def get_table_description(self, connection, cursor, table_name):
        """
        Returns a description of the table, with the DB-API cursor.description interface."
        """
        # varchar length returned by cursor.description is an internal length,
        # not visible length (#5725), use information_schema database to fix this
        cursor.execute("""
            SELECT column_name, character_maximum_length, column_comment, column_default, data_type
 FROM information_schema.columns
            WHERE table_name = %s AND table_schema = DATABASE()
                AND character_maximum_length IS NOT NULL""", [table_name])
        
        length_map = {}
        comment_map = {}
        default_map = {}
        all = cursor.fetchall()
        for name, length, comment, default_value, data_type in all:
            length_map[name] = length
            comment_map[name] = comment
            data_type = data_type.lower()
            if data_type.find('int') != -1:
                default_value = int(default_value)
            elif data_type.find('float') != -1:
                default_value = float(default_value)
            default_map[name] = default_value


        cursor.execute("SELECT * FROM %s LIMIT 1" % connection.ops.quote_name(table_name))

        all_res = []
        for line in cursor.description:
            res = []
            name = line[0]
            res.extend(line[:3])
            res.append(length_map.get(name, line[3]))
            res.extend(line[4:])
            res.append(comment_map.get(name, ''))
            res.append(default_map.get(name, None))
            all_res.append(res)
        return all_res

