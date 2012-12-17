
from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^ajax_lookup/(?P<channel>[-\w]+)$',
        'pycomm.django_apps.ajax_select.views.ajax_lookup',
        name = 'ajax_lookup'
    ),
    url(r'^add_popup/(?P<app_label>\w+)/(?P<model>\w+)$',
        'pycomm.django_apps.ajax_select.views.add_popup',
        name = 'add_popup'
    )
)

