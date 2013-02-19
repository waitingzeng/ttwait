from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import exadmin
exadmin.autodiscover()

from exadmin.plugins import xversion
xversion.registe_models()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'custom.views.home', name='home'),
    # url(r'^custom/', include('custom.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^diygl/', include(exadmin.site.urls)),
)
