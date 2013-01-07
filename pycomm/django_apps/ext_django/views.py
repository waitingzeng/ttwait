# Create your views here.
from django.views.decorators.cache import never_cache
import django.utils.simplejson as simplejson
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.db import models
from pycomm.log import log


@never_cache
def model_lookup(request):
    if not (request.user.is_active and request.user.is_staff):
        return HttpResponseForbidden('<h1>Permission denied</h1>')
    data = []
    if request.method == 'GET':
        params = dict(request.GET)
        for k, v in params.items():
            params[k] = v[0]

        log.trace("params %s", params)
        app_label = params.pop('app_label', None)
        model_name = params.pop('model_name', None)
        if app_label and model_name:
            try:
                model = models.get_model(app_label, model_name)
                obj = model.objects.get(**params)
                return HttpResponse(simplejson.dumps(obj.json_data()), mimetype='application/javascript')
            except:
                log.exception()
                pass
        else:
            log.error("params error")
    data = {}
    return HttpResponse(simplejson.dumps(data), mimetype='application/javascript')

