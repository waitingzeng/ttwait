from django.core.management.base import AppCommand
from django.db import models

from pycomm.django_apps.djangosphinx.models import SphinxModelManager
from pycomm.django_apps.djangosphinx.utils.config import generate_config_for_model


class Command(AppCommand):
    help = "Prints generic configuration for any models which use a standard SphinxSearch manager."

    output_transaction = True

    def handle_app(self, app, **options):
        try:
                
            model_classes = [getattr(app, n) for n in dir(app) if hasattr(getattr(app, n), '_meta')]
            found = 0
            for model in model_classes:
                indexes = getattr(model, '__sphinx_indexes__', [])
                for index in indexes:
                    found += 1
                    print generate_config_for_model(model, index)
                    
            if found == 0:
                print "Unable to find any models in application which use standard SphinxSearch configuration."
            #return u'\n'.join(sql_create(app, self.style)).encode('utf-8')
        except:
            import traceback
            traceback.print_exc()
            raise
