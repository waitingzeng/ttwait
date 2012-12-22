#! /usr/bin/env python
#coding=utf-8
from optparse import make_option
from django.core.management.base import NoArgsCommand
from django.core.management.color import no_style
from django.db import connections, router, models, DEFAULT_DB_ALIAS
import copy

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Nominates a database to alter. '
                'Defaults to the "default" database.'),
        make_option('--model', action='store', dest='model',
            default='', help='Nominates a model to alter. '
                'Defaults to the all model'),
        make_option('--autodel', action='store', dest='autodel',
                    default=False, help='Auto delele column, default is True'),
        
    )
    help = "Alter the database tables for all apps in INSTALLED_APPS whose tables have some column change.\nadd new column if is a ForeignKey must be null, if a normal column must be null or give a default value"

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.indexs = {}

    def load_db_column(self, table):
        sql = 'SHOW FIELDS FROM %s' % table
        self.cursor.execute(sql)
        columns = self.cursor.fetchall()
        return dict([(x[0], x[1]) for x in columns])
    
    def load_db_indexs(self, table):
        
        sql = 'SHOW INDEX FROM %s' % table
        self.cursor.execute(sql)
        self.indexs[table] = self.cursor.fetchall()
        
    def find_index(self, table, col):
        indexs = self.indexs.setdefault(table, self.load_db_indexs(table))
        all_indexs = []
        for index in indexs:
            if col in index[4]:
                all_indexs.append(index[2])
        return all_indexs
    
    def is_same_col_type(self, model_type, db_type):
        if model_type == db_type:
            return True
        if model_type[:3] == 'int' and db_type.find('int') != -1:
            return True
        if model_type[:4] == 'bool' and db_type.find('int') != -1:
            return True
        if model_type[:7] == 'varchar' and db_type.find('varchar') != -1:
            return True
        if model_type[:8] == 'smallint' and db_type.find('smallint') != -1:
            return True
        if model_type[:6] == 'double' and db_type.find('double') != -1:
            return True
        return False
    
    def get_change_col(self, db_remove, col_type):
        for col, _type in db_remove.items():
            if self.is_same_col_type(col_type, _type):
                return col
        return None
    
    def sql_alter_model(self, model, connection, known_models=set()):
        pending_references = {}
        
        table_output = []
        qn = connection.ops.quote_name
        opts = model._meta
        db_columns = self.load_db_column(opts.db_table)
        db_remove = copy.copy(db_columns)
        for f in opts.local_fields:
            if f.column in db_columns:
                db_remove.pop(f.column)
        
        for f in opts.local_fields:
            col_type = f.db_type(connection=connection)
            if col_type is None:
                continue
            col_type = self.style.SQL_COLTYPE(col_type)
            
            if f.column in db_columns:
                _type = db_columns[f.column]
                if not self.is_same_col_type(col_type, _type):
                    field_output = [' change ', self.style.SQL_FIELD(qn(f.column)), self.style.SQL_FIELD(qn(f.column)),
                                    col_type]
                    table_output.append(' '.join(field_output))
                    
                continue
            
            change_col = None#self.get_change_col(db_remove, col_type)
            
            f.default = models.NOT_PROVIDED
            f.null = True
            
            
            tablespace = f.db_tablespace or opts.db_tablespace
            
            if change_col:
                field_output = [' change ', change_col, self.style.SQL_FIELD(qn(f.column)), col_type]
            else:
                
                field_output = ['add column', self.style.SQL_FIELD(qn(f.column)),
                    col_type]
            
            if not f.null:
                field_output.append(self.style.SQL_KEYWORD('NOT NULL'))
            if f.rel:
                ref_output, pending = connection.creation.sql_for_inline_foreign_key_references(f, known_models, self.style)
                if pending:
                    pr = pending_references.setdefault(f.rel.to, []).append((model, f))
                else:
                    field_output.extend(ref_output)
            table_output.append(' '.join(field_output))
        
        if self.autodel:
            for col in db_remove.keys():
                all_indexs = self.find_index(opts.db_table, col)
                for index in all_indexs:
                    table_output.append('DROP FOREIGN KEY %s' % index)
                    table_output.append('DROP INDEX %s' % index)
                
                table_output.append('DROP %s' % self.style.SQL_FIELD(qn(col)))
        
        full_output = []
        for sql in table_output:
            full_output.append('ALTER TABLE %s %s' % (self.style.SQL_TABLE(qn(opts.db_table)), sql))
        
        return full_output, pending_references
    

    def handle_noargs(self, **options):

        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive')
        show_traceback = options.get('traceback', False)
        self.autodel = options.get('autodel', True)

        self.style = no_style()

        db = options.get('database', DEFAULT_DB_ALIAS)
        target_model = options.get('model', '').lower()
        connection = connections[db]
        self.cursor = connection.cursor()

        # Get a list of already installed *models* so that references work right.
        tables = connection.introspection.table_names()
        seen_models = connection.introspection.installed_models(tables)
        pending_references = {}
        
        all_models = [
            (app.__name__.split('.')[-2],
                [m for m in models.get_models(app, include_auto_created=True)
                if router.allow_syncdb(db, m)])
            for app in models.get_apps()
        ]

        # Alter the tables for each model
        for app_name, model_list in all_models:
            if app_name and app_name != db:
                continue

            for model in model_list:
                if target_model and not model.__name__.lower().startswith(target_model):
                    continue
                sql, references = self.sql_alter_model(model, connection)
                if not sql:
                    continue
                for refto, refs in references.items():
                    pending_references.setdefault(refto, []).extend(refs)
                    if refto in seen_models:
                        sql.extend(connection.creation.sql_for_pending_references(refto, self.style, pending_references))
                sql.extend(connection.creation.sql_for_pending_references(model, self.style, pending_references))
                
                for statement in sql:
                    print statement
                    try:
                        self.cursor.execute(statement)
                    except Exception, info:
                        print info
