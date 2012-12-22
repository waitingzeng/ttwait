#!/usr/bin/python
#coding=utf8
from optparse import make_option
from django.core.management.base import NoArgsCommand, AppCommand
from django.core.management.color import no_style
from django.db import connections, router, models, DEFAULT_DB_ALIAS
import copy
from django.core.management.base import CommandError
from django.db.backends.mysql.creation import DatabaseCreation
from django.db.models.fields import NOT_PROVIDED



class MysqlCreation(DatabaseCreation):
    def sql_create_model(self, model, style, known_models=set()):
        """
        Returns the SQL required to create a single model, as a tuple of:
            (list_of_sql, pending_references_dict)
        """
        opts = model._meta
        if not opts.managed or opts.proxy or opts.swapped:
            return [], {}
        final_output = []
        table_output = []
        pending_references = {}
        qn = self.connection.ops.quote_name
        charset = self.connection.settings_dict.get('CHARSET', 'utf8')
        dbengine = self.connection.settings_dict.get('DBENGINE', 'MyISAM')
        
        for f in opts.local_fields:
            col_type = f.db_type(connection=self.connection)
            if col_type is None:
                # Skip ManyToManyFields, because they're not represented as
                # database columns in this table.
                continue
            # Make the definition (e.g. 'foo VARCHAR(30)') for this field.
            field_output = [style.SQL_FIELD(qn(f.column)),
                style.SQL_COLTYPE(col_type)]
            # Oracle treats the empty string ('') as null, so coerce the null
            # option whenever '' is a possible value.
            null = f.null
            if (f.empty_strings_allowed and not f.primary_key and
                    self.connection.features.interprets_empty_strings_as_nulls):
                null = True
            if not null:
                field_output.append(style.SQL_KEYWORD('NOT NULL'))
            if f.default != NOT_PROVIDED and isinstance(f.default, (int, float, long, basestring)):
                field_output.append('DEFAULT %s' % repr(f.default))
            if f.primary_key:
                field_output.append(style.SQL_KEYWORD('PRIMARY KEY'))
            elif f.unique:
                field_output.append(style.SQL_KEYWORD('UNIQUE'))
            if f.rel:
                ref_output, pending = self.sql_for_inline_foreign_key_references(
                    f, known_models, style)
                if pending:
                    pending_references.setdefault(f.rel.to, []).append(
                        (model, f))
                else:
                    field_output.extend(ref_output)

            if f.verbose_name and f.verbose_name != f.column:
                field_output.append('COMMENT "%s"' % f.verbose_name)

            table_output.append(' '.join(field_output))
        for field_constraints in opts.unique_together:
            table_output.append(style.SQL_KEYWORD('UNIQUE') + ' (%s)' %
                ", ".join(
                    [style.SQL_FIELD(qn(opts.get_field(f).column))
                     for f in field_constraints]))

        full_statement = [style.SQL_KEYWORD('CREATE TABLE') + ' ' +
                          style.SQL_TABLE(qn(opts.db_table)) + ' (']
        for i, line in enumerate(table_output):  # Combine and add commas.
            full_statement.append(
                '    %s%s' % (line, i < len(table_output) - 1 and ',' or ''))
        full_statement.append(')ENGINE %s DEFAULT CHARSET=%s;' % (dbengine, charset))
        final_output.append('\n'.join(full_statement))

        if opts.has_auto_field:
            # Add any extra SQL needed to support auto-incrementing primary
            # keys.
            auto_column = opts.auto_field.db_column or opts.auto_field.name
            autoinc_sql = self.connection.ops.autoinc_sql(opts.db_table,
                                                          auto_column)
            if autoinc_sql:
                for stmt in autoinc_sql:
                    final_output.append(stmt)

        return final_output, pending_references


def sql_create(app, model_name, style, connection):
    "Returns a list of the CREATE TABLE SQL statements for the given app and model."

    if connection.settings_dict['ENGINE'] == 'django.db.backends.dummy':
        # This must be the "dummy" database backend, which means the user
        # hasn't set ENGINE for the database.
        raise CommandError("Django doesn't know which syntax to use for your SQL statements,\n" +
            "because you haven't specified the ENGINE setting for the database.\n" +
            "Edit your settings file and change DATBASES['default']['ENGINE'] to something like\n" +
            "'django.db.backends.postgresql' or 'django.db.backends.mysql'.")

    # Get installed models, so we generate REFERENCES right.
    # We trim models from the current app so that the sqlreset command does not
    # generate invalid SQL (leaving models out of known_models is harmless, so
    # we can be conservative).
    app_models = models.get_models(app, include_auto_created=True)
    final_output = []
    tables = connection.introspection.table_names()
    known_models = set([model for model in connection.introspection.installed_models(tables) if model not in app_models])
    pending_references = {}

    model_name = model_name and model_name.lower() or ''

    connection.creation = MysqlCreation(connection)

    for model in app_models:
        if model_name and not model.__name__.lower().startswith(model_name):
            continue
        output, references = connection.creation.sql_create_model(model, style, known_models)

        final_output.extend(output)
        for refto, refs in references.items():
            pending_references.setdefault(refto, []).extend(refs)
            if refto in known_models:
                final_output.extend(connection.creation.sql_for_pending_references(refto, style, pending_references))
        final_output.extend(connection.creation.sql_for_pending_references(model, style, pending_references))
        final_output.append('\r\n\r\n')
        # Keep track of the fact that we've created the table for this model.
        known_models.add(model)

    # Handle references to tables that are from other apps
    # but don't exist physically.
    not_installed_models = set(pending_references.keys())
    if not_installed_models:
        alter_sql = []
        for model in not_installed_models:
            alter_sql.extend(['-- ' + sql for sql in
                connection.creation.sql_for_pending_references(model, style, pending_references)])
        if alter_sql:
            final_output.append('-- The following references should be added but depend on non-existent tables:')
            final_output.extend(alter_sql)

    return final_output
