

from .fields import autoselect_fields_check_can_add
from pycomm.django_apps.ext_django import admin

class AjaxSelectAdmin(admin.ModelAdmin):

    """ in order to get + popup functions subclass this or do the same hook inside of your get_form """

    def get_form(self, request, obj=None, **kwargs):
        form = super(AjaxSelectAdmin,self).get_form(request,obj,**kwargs)

        autoselect_fields_check_can_add(form,self.model,request.user)
        return form

