#!/usr/bin/python
#coding=utf8

from django.db import models
import manager
from django.utils import six
from django.db.models import base
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor, ReverseManyRelatedObjectsDescriptor, ForeignKey, \
    ReverseSingleRelatedObjectDescriptor
from django.db.models.base import ModelBase
from django.core.urlresolvers import reverse
from django.utils import six

# Create your models here.

class NewBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        ret = ModelBase.__new__(cls, name, bases, attrs)
        if hasattr(ret, 'init_related_lookup'):
                ret.init_related_lookup()
        return ret


class BaseModel(six.with_metaclass(NewBase), models.Model):

    objects = manager.ModelManager()

    full_info_fields = []
    simple_info_fields = []
    foreign_key_fields = []
    show_json_comment = True

    had_init_related_lookup = False
    class Meta:
        abstract = True


    @classmethod
    def find_field(cls, name):
        for field in cls._meta.local_fields:
            if field.name == name:
                return field
        return None

    @classmethod
    def get_full_info_fields(cls):
        if not cls.full_info_fields:
            cls.full_info_fields = [x.name for x in cls._meta.local_fields]
        return cls.full_info_fields

    @classmethod
    def get_simple_info_fields(cls):
        if not cls.simple_info_fields:
            cls.simple_info_fields = []
            for x in cls._meta.local_fields:
                if not x.editable:
                    continue
                if isinstance(x, (models.ForeignKey, models.TextField)):
                    continue
                cls.simple_info_fields.append(x.name)

        return cls.simple_info_fields

    def _get_field_data(self, name):
        if name.find('.') != -1:
            name, extra = name.split('.')
            is_simple_info = extra != 'full'
        else:
            is_simple_info = getattr(self._state, 'is_simple_info', True)
        
        field = self.find_field(name)
        if not hasattr(self, name):
            return None
        if field:
            short_desc = field.verbose_name
        else:
            short_desc = ''

        v = getattr(self, name)
        if not v:
            return name, None, short_desc
        if isinstance(field, models.ForeignKey):
            v._state.is_simple_info = is_simple_info
            v = v.json_data()
        elif repr(v).find('RelatedManager') != -1:
            fks = []
            for x in v.all():
                x._state.is_simple_info = is_simple_info
                fks.append(x.json_data())
            v = fks
        else:
            if hasattr(v, '__name__'):
                name = v.__name__
            if hasattr(v, 'short_description'):
                short_desc = v.short_description
            if callable(v):
                v = v()
        return name, v, short_desc

    def _get_fields_data(self, fieldset):

        res = {}
        comments = {}
        for fields in fieldset:
            if isinstance(fields, basestring):
                ret = self._get_field_data(fields)
                if not ret:
                    continue
                res[ret[0]] = ret[1]
                if self.show_json_comment:
                    comments[ret[0]] = ret[2]
            else:
                name, fields = fields
                res[name] = {}
                comments[name] = {}
                for field in fields:
                    ret = self._get_field_data(field)
                    if not ret:
                        continue
                    res[name][ret[0]] = ret[1]
                    if self.show_json_comment:
                        comments[name][ret[0]] = ret[2]

        if self.show_json_comment:
            res['_comments'] = comments
        return res

    def full_info(self):
        return self._get_fields_data(self.__class__.get_full_info_fields())


    def simple_info(self):
        return self._get_fields_data(self.__class__.get_simple_info_fields())

    def simple(self):
        self._state.is_simple_info = True

    def full(self):
        self._state.is_simple_info = False

    def json_data(self):
        if getattr(self._state, 'is_simple_info', True):
            return self.simple_info()
        return self.full_info()


    @classmethod
    def init_related_lookup(cls):
        if not hasattr(cls, '_meta'):
            return
        #if cls.had_init_related_lookup:
        #    return
        cls.had_init_related_lookup = True
        for k, v in cls.__dict__.items():
            
            if isinstance(v, ReverseSingleRelatedObjectDescriptor):
                func_name = 'show_%s' % cls.__name__.lower()
                to_model = v.field.rel.to
                if isinstance(to_model, basestring):
                    continue
                if not hasattr(to_model, func_name):
                    def _func(self, target=cls, v=v):
                        view_url = 'admin:%s_%s_changelist' % (cls._meta.app_label, cls._meta.module_name)
                        try:
                            url = reverse(view_url)
                        except:
                            import traceback
                            traceback.print_exc()
                            return ''
                        return '<a href="%s?%s__id__exact=%s" target="_blank">查看</a>' % (url, v.field.name, self.pk)
                    _func.__name__ = str(cls._meta.verbose_name)
                    _func.allow_tags = True
                    setattr(to_model, func_name, _func)
            elif isinstance(v, ReverseManyRelatedObjectsDescriptor):
                func_name = 'get_%s_all_display' % k
                to_model = v.field.rel.to
                if not hasattr(cls, func_name):
                    def _func(self, k=k, v=v):
                        return ','.join([unicode(x) for x in getattr(self, k).all()])
                    _func.__name__ = str(v.field.verbose_name)
                    setattr(cls, func_name, _func)

                func_name = 'show_%s' % cls.__name__.lower()
                to_model = v.field.rel.to
                if isinstance(to_model, basestring):
                    continue
                if not hasattr(to_model, func_name):
                    def _func(self, target=cls, v=v):
                        view_url = 'admin:%s_%s_changelist' % (cls._meta.app_label, cls._meta.module_name)
                        try:
                            url = reverse(view_url)
                        except:
                            import traceback
                            traceback.print_exc()
                            return ''
                        return '<a href="%s?%s__id__exact=%s" target="_blank">查看</a>' % (url, v.field.name, self.pk)
                    _func.__name__ = str(cls._meta.verbose_name)
                    _func.allow_tags = True
                    setattr(to_model, func_name, _func)


BaseModel._meta.local_fields = []

models.Model = BaseModel

from MySQLdb.constants import FIELD_TYPE, CLIENT

def typecast_decimal(s):
    if s is None or s == '':
        return None
    return float(s)

from django.db.backends.mysql.base import django_conversions
django_conversions.update({
    FIELD_TYPE.DECIMAL: typecast_decimal,
    FIELD_TYPE.NEWDECIMAL: typecast_decimal,
})
