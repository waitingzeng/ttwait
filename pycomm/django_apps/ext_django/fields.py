#coding=utf8
import uuid
import urlparse
import datetime
import time
import os
import random
import re


from django.contrib.admin import util
from django import forms
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.html import conditional_escape, format_html, format_html_join, mark_safe
from django.forms.util import flatatt, to_current_timezone
from django.contrib.admin import util
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor
from django.template.defaultfilters import slugify
from django.db.models import DateTimeField, CharField, SlugField
from django.utils.text import capfirst
from django.conf import settings


try:
    from django.utils.timezone import now as datetime_now
except ImportError:
    import datetime
    datetime_now = datetime.datetime.now


import ujson as json

from pycomm.utils.pprint import pformat

from widget import AdminImageWidget


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

        if auto_now or auto_now_add:
            kwargs['editable'] = False
            kwargs['blank'] = True
        self.isnull = True
        kwargs['auto_now'] = auto_now
        kwargs['auto_now_add'] = auto_now_add
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


    def contribute_to_class(self, cls, name):
        super(UnixTimestampField, self).contribute_to_class(cls, name)
        def func(obj, fieldname=name):
            value = getattr(obj,fieldname)
            if isinstance(value, (int, long)):
                return datetime.datetime.fromtimestamp(value)
            return value
        func.__name__ = self.verbose_name
        setattr(cls, 'get_%s_display' % self.name, func)


#    def value_from_object(self, obj):
#        value = super(UnixTimestampField, self).value_from_object(obj)
#        if isinstance(value, int):
#            return datetime.datetime.fromtimestamp(value)
#        return value
models.UnixTimestampField = UnixTimestampField


class ZeroReverseSingleRelatedObjectDescriptor(ReverseSingleRelatedObjectDescriptor):
    def __get__(self, instance, instance_type=None):
        try:
            return ReverseSingleRelatedObjectDescriptor.__get__(self, instance, instance_type)
        except self.field.rel.to.DoesNotExist:
            return None
       

class ZeroForeignKey(models.ForeignKey):
    def get_db_prep_save(self, value, connection):
        if value == '' or value == None:
            return 0
        elif value == 0:
            return 0
        else:
            return self.rel.get_related_field().get_db_prep_save(value,
                connection=connection)

    def contribute_to_class(self, cls, name):
        super(ZeroForeignKey, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ZeroReverseSingleRelatedObjectDescriptor(self))

models.ZeroForeignKey = ZeroForeignKey


from pycomm.utils.cache import SimpleFileBasedCache


class CustomImageField(models.ImageField):
    def get_filename(self, filename):
        key = '%s%s' % (random.random(), filename)
        return SimpleFileBasedCache.name_to_key(key, '.jpg')

    def __unicode__(self):
        return ''


    def contribute_to_class(self, cls, name):
        super(CustomImageField, self).contribute_to_class(cls, name)
        def func(obj, fieldname=name):
            value = getattr(obj,fieldname)
            if not value:
                return ''

            value = urlparse.urljoin(settings.MEDIA_URL, value)
            return mark_safe('<a target="_blank" href="%(value)s"><img src="%(value)s" width="100px" /></a>' % locals())
        func.__name__ = self.verbose_name
        setattr(cls, 'get_%s_display' % self.name, func)





class AutoSlugField(SlugField):
    """ AutoSlugField

    By default, sets editable=False, blank=True.

    Required arguments:

    populate_from
        Specifies which field or list of fields the slug is populated from.

    Optional arguments:

    separator
        Defines the used separator (default: '-')

    overwrite
        If set to True, overwrites the slug on every save (default: False)

    Inspired by SmileyChris' Unique Slugify snippet:
    http://www.djangosnippets.org/snippets/690/
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('editable', False)

        populate_from = kwargs.pop('populate_from', None)
        if populate_from is None:
            raise ValueError("missing 'populate_from' argument")
        else:
            self._populate_from = populate_from
        self.separator = kwargs.pop('separator', u'-')
        self.overwrite = kwargs.pop('overwrite', False)
        self.allow_duplicates = kwargs.pop('allow_duplicates', False)
        super(AutoSlugField, self).__init__(*args, **kwargs)

    def _slug_strip(self, value):
        """
        Cleans up a slug by removing slug separator characters that occur at
        the beginning or end of a slug.

        If an alternate separator is used, it will also replace any instances
        of the default '-' separator with the new separator.
        """
        re_sep = '(?:-|%s)' % re.escape(self.separator)
        value = re.sub('%s+' % re_sep, self.separator, value)
        return re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)

    def slugify_func(self, content):
        if content:
            return slugify(content)
        return ''

    def create_slug(self, model_instance, add):
        # get fields to populate from and slug field to set
        if not isinstance(self._populate_from, (list, tuple)):
            self._populate_from = (self._populate_from, )
        slug_field = model_instance._meta.get_field(self.attname)

        if add or self.overwrite:
            # slugify the original field content and set next step to 2
            slug_for_field = lambda field: self.slugify_func(getattr(model_instance, field))
            slug = self.separator.join(map(slug_for_field, self._populate_from))
            next = 2
        else:
            # get slug from the current model instance
            slug = getattr(model_instance, self.attname)
            # model_instance is being modified, and overwrite is False,
            # so instead of doing anything, just return the current slug
            return slug

        # strip slug depending on max_length attribute of the slug field
        # and clean-up
        slug_len = slug_field.max_length
        if slug_len:
            slug = slug[:slug_len]
        slug = self._slug_strip(slug)
        original_slug = slug

        if self.allow_duplicates:
            return slug

        # exclude the current model instance from the queryset used in finding
        # the next valid slug
        queryset = model_instance.__class__._default_manager.all()
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        # form a kwarg dict used to impliment any unique_together contraints
        kwargs = {}
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                for param in params:
                    kwargs[param] = getattr(model_instance, param, None)
        kwargs[self.attname] = slug

        # increases the number while searching for the next valid slug
        # depending on the given slug, clean-up
        while not slug or queryset.filter(**kwargs):
            slug = original_slug
            end = '%s%s' % (self.separator, next)
            end_len = len(end)
            if slug_len and len(slug) + end_len > slug_len:
                slug = slug[:slug_len - end_len]
                slug = self._slug_strip(slug)
            slug = '%s%s' % (slug, end)
            kwargs[self.attname] = slug
            next += 1
        return slug

    def pre_save(self, model_instance, add):
        value = unicode(self.create_slug(model_instance, add))
        setattr(model_instance, self.attname, value)
        return value

    def get_internal_type(self):
        return "SlugField"

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = '%s.AutoSlugField' % self.__module__
        args, kwargs = introspector(self)
        kwargs.update({
            'populate_from': repr(self._populate_from),
            'separator': repr(self.separator),
            'overwrite': repr(self.overwrite),
            'allow_duplicates': repr(self.allow_duplicates),
        })
        # That's our definition!
        return (field_class, args, kwargs)
models.AutoSlugField = AutoSlugField


class UUIDVersionError(Exception):
    pass


class UUIDField(CharField):
    """ UUIDField

    By default uses UUID version 1 (generate from host ID, sequence number and current time)

    The field support all uuid versions which are natively supported by the uuid python module.
    For more information see: http://docs.python.org/lib/module-uuid.html
    """

    def __init__(self, verbose_name=None, name=None, auto=True, version=1, node=None, clock_seq=None, namespace=None, **kwargs):
        kwargs['max_length'] = 36
        if auto:
            self.empty_strings_allowed = False
            kwargs['blank'] = True
            kwargs.setdefault('editable', False)
        self.auto = auto
        self.version = version
        if version == 1:
            self.node, self.clock_seq = node, clock_seq
        elif version == 3 or version == 5:
            self.namespace, self.name = namespace, name
        CharField.__init__(self, verbose_name, name, **kwargs)

    def get_internal_type(self):
        return CharField.__name__

    def contribute_to_class(self, cls, name):
        if self.primary_key:
            assert not cls._meta.has_auto_field, \
              "A model can't have more than one AutoField: %s %s %s; have %s" % \
               (self, cls, name, cls._meta.auto_field)
            super(UUIDField, self).contribute_to_class(cls, name)
            cls._meta.has_auto_field = True
            cls._meta.auto_field = self
        else:
            super(UUIDField, self).contribute_to_class(cls, name)

    def create_uuid(self):
        if not self.version or self.version == 4:
            return uuid.uuid4()
        elif self.version == 1:
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version == 2:
            raise UUIDVersionError("UUID version 2 is not supported.")
        elif self.version == 3:
            return uuid.uuid3(self.namespace, self.name)
        elif self.version == 5:
            return uuid.uuid5(self.namespace, self.name)
        else:
            raise UUIDVersionError("UUID version %s is not valid." % self.version)

    def pre_save(self, model_instance, add):
        value = super(UUIDField, self).pre_save(model_instance, add)
        if self.auto and add and value is None:
            value = unicode(self.create_uuid())
            setattr(model_instance, self.attname, value)
            return value
        else:
            if self.auto and not value:
                value = unicode(self.create_uuid())
                setattr(model_instance, self.attname, value)
        return value
    
    def formfield(self, **kwargs):
        if self.auto:
            return None
        super(UUIDField, self).formfield(**kwargs)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.CharField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)
models.UUIDField = UUIDField


from django.db import models
from django import forms

class MultiSelectFormField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple
    
    def __init__(self, *args, **kwargs):
        self.max_choices = kwargs.pop('max_choices', 0)
        super(MultiSelectFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        if value and self.max_choices and len(value) > self.max_choices:
            raise forms.ValidationError('You must select a maximum of %s choice%s.'
                    % (apnumber(self.max_choices), pluralize(self.max_choices)))
        return value

class MultiSelectField(models.Field):
    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return "CharField"

    def get_choices_default(self):
        return self.get_choices(include_blank=False)

    def _get_FIELD_display(self, field):
        value = getattr(self, field.attname)
        choicedict = dict(field.choices)

    def formfield(self, **kwargs):
        # don't call super, as that overrides default widget if it has choices
        defaults = {'required': not self.blank, 'label': capfirst(self.verbose_name), 
                    'help_text': self.help_text, 'choices':self.choices}
        if self.has_default():
            defaults['initial'] = self.get_default()
        defaults.update(kwargs)
        return MultiSelectFormField(**defaults)

    def get_db_prep_value(self, value, connection, prepared):
        if not value:
            return ''
        if isinstance(value, basestring):
            return value
        elif isinstance(value, list):
            return ",".join(value) + ','

    def to_python(self, value):
        if isinstance(value, list):
            return value
        if not value:
            return []
        return value.strip(',').split(",")

    def contribute_to_class(self, cls, name):
        super(MultiSelectField, self).contribute_to_class(cls, name)
        if self.choices:
            func = lambda self, fieldname = name, choicedict = dict(self.choices):",".join([choicedict.get(value,value) for value in getattr(self,fieldname)])
            setattr(cls, 'get_%s_display' % self.name, func)


    def validate(self, value, model_instance):
        if not self.editable:
            # Skip validation for non-editable fields.
            return

        for item in value:
            super(MultiSelectField, self).validate(item, model_instance)
        return
models.MultiSelectField = MultiSelectField
