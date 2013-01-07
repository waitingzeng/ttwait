from django.db.models import get_model
from django.http import HttpResponse
import json as simplejson
import locale
from .utils import unicode_sorter

def filterchain(request, app, model, field, value, manager=None):
    Model = get_model(app, model)
    if value == '0':
        keywords = {str("%s__isnull" % field):True}
    else:
        keywords = {str(field): str(value)}

    params = dict(request.GET)
    for k, v in params.items():
        params[k] = v[0]

    keywords.update(params)    

    if manager is not None and hasattr(Model, manager):
        queryset = getattr(Model, manager).all()
    else:
        queryset = Model.objects
    results = list(queryset.filter(**keywords))
    results.sort(cmp=locale.strcoll, key=lambda x:unicode_sorter(unicode(x)))
    result = []
    for item in results:
        result.append({'value':item.pk, 'display':unicode(item)})
    json = simplejson.dumps(result)
    return HttpResponse(json, mimetype='application/json')

def filterchain_all(request, app, model, field, value):
    Model = get_model(app, model)
    if value == '0':
        keywords = {str("%s__isnull" % field):True}
    else:
        keywords = {str(field): str(value)}
    results = list(Model.objects.filter(**keywords))
    results.sort(cmp=locale.strcoll, key=lambda x:unicode_sorter(unicode(x)))
    final = []
    for item in results:
        final.append({'value':item.pk, 'display':unicode(item)})
    results = list(Model.objects.exclude(**keywords))
    results.sort(cmp=locale.strcoll, key=lambda x:unicode_sorter(unicode(x)))
    final.append({'value':"", 'display':"---------"})

    for item in results:
        final.append({'value':item.pk, 'display':unicode(item)})
    json = simplejson.dumps(final)
    return HttpResponse(json, mimetype='application/json')
