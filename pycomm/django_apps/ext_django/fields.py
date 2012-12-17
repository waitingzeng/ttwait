#coding=utf8

from django.contrib.admin import util

from django import forms
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.html import conditional_escape, format_html, format_html_join, mark_safe
from django.forms.util import flatatt, to_current_timezone
from django.contrib.admin import util
from pycomm.utils.pprint import pformat
import datetime
import ujson as json
import time


class ImageURLWidget(forms.widgets.TextInput):

    """  widget to select a model and return it as text """

    input_type = 'img'
    def __init__(self, show_width, show_height, *args, **kwargs):
        forms.widgets.TextInput.__init__(self, *args, **kwargs)
        self.show_height = show_height
        self.show_width = show_width
        self.attrs['width'] = self.show_width
        self.attrs['height'] = self.show_height

    def render(self, name, value, attrs=None):

        value = value or ''

        final_attrs = self.build_attrs(attrs)
        return format_html('<a href="{0}" target="_blank"><img src="{0}" {1} /></a>', value, flatatt(final_attrs))


class ImageURLField(forms.URLField):
    def __init__(self, show_width=100, show_height=100, *args, **kwargs):
        self.show_width, self.show_height = show_width, show_height

        widget = kwargs.get("widget", False)

        if not widget or not isinstance(widget, ImageURLWidget):
            widget_kwargs = dict(
                show_width = self.show_width,
                show_height = self.show_height,
            )
            kwargs["widget"] = ImageURLWidget(**widget_kwargs)
        super(ImageURLField, self).__init__(*args, **kwargs)

   

class ImageURLDBField(models.CharField):
    def __init__(self, *args, **kwargs):
        self.show_width = kwargs.pop('show_width', 100)
        self.show_height = kwargs.pop('show_height', 100)
        return models.CharField.__init__(self, *args, **kwargs)


    def formfield(self, form_class=ImageURLField, **kwargs):
        kwargs['show_width'] = self.show_width
        kwargs['show_height'] = self.show_height
        kwargs['form_class'] = form_class

        return models.CharField.formfield(self, **kwargs)

models.ImageURLDBField = ImageURLDBField


class JSONTextWidget(forms.widgets.TextInput):

    """  widget to select a model and return it as text """

    input_type = 'textarea'
    def render(self, name, value, attrs=None):

        if isinstance(value, (str, unicode)):
            value = json.loads(value)

        return mark_safe("""<pre>

            
%s</pre>""" % (pformat(value)))


class JSONTextField(forms.CharField):
    def __init__(self, *args, **kwargs):
        widget = kwargs.get("widget", False)

        if not widget or not isinstance(widget, JSONTextWidget):
            kwargs["widget"] = JSONTextWidget()
        forms.CharField.__init__(self, *args, **kwargs)

   

class JSONTextField(models.TextField):
    def formfield(self, form_class=JSONTextField, **kwargs):
        kwargs['form_class'] = form_class
        return models.TextField.formfield(self, **kwargs)


models.JSONTextField = JSONTextField

class UnixTimestampField(models.DateTimeField):
    """UnixTimestampField: creates a DateTimeField that is represented on the
    database as a TIMESTAMP field rather than the usual DATETIME field.
    """
    def __init__(self, verbose_name='',  auto_now=False,
                 auto_now_add=False,  **kwargs):

        self.auto_now, self.auto_now_add = auto_now, auto_now_add
        if auto_now or auto_now_add:
            kwargs['editable'] = False
            kwargs['blank'] = True
        self.isnull = True
        super(UnixTimestampField, self).__init__(verbose_name, **kwargs)
        
    def db_type(self, connection):
        typ=['TIMESTAMP']
        # See above!
        if self.isnull:
            typ += ['NULL']
        if self.auto_now_add:
            typ += ['default CURRENT_TIMESTAMP']
        if self.auto_now:
             typ += ['on update CURRENT_TIMESTAMP']
        return ' '.join(typ)
    
models.UnixTimestampField = UnixTimestampField



class ZeroForeignKey(models.ForeignKey):
    def get_db_prep_save(self, value, connection):
        if value == '' or value == None:
            return None
        elif value == 0:
            return 0
        else:
            return self.rel.get_related_field().get_db_prep_save(value,
                connection=connection)

models.ZeroForeignKey = ZeroForeignKey
