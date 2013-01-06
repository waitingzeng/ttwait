from django.db import models
import manager
from django.utils import six
from django.db.models import base

# Create your models here.

class BaseModel(models.Model):
    objects = manager.ModelManager()

    full_info_fields = []
    simple_info_fields = []
    foreign_key_fields = []

    class Meta:
        abstract = True


    @classmethod
    def find_field(self, name):
        for field in self._meta.local_fields:
            if field.name == name:
                return field
        return None

    @classmethod
    def get_extra_fields(cls, simple=True):
        if not hasattr(cls, '_extra_simple_fields'):
            cls._extra_simple_fields = []
            cls._extra_full_fileds = []
            for name, value in cls.__dict__.items():
                if name.startswith('_'):
                    continue
                if callable(value):
                    if getattr(value, 'simple_info', None):
                        cls._extra_simple_fields.append(name)

                    if getattr(value, 'full_info', None):
                        cls._extra_full_fileds.append(name)
            cls.foreign_key_fields = [field.name for field in cls._meta.local_fields if isinstance(field, models.ForeignKey)]
        if simple:
            return cls._extra_simple_fields
        return cls._extra_full_fileds + cls._extra_simple_fields


    def get_full_info_fields(self):
        if not self.full_info_fields:
            self.full_info_fields = [x.column for x in self._meta.local_fields]
        return self.full_info_fields + self.__class__.get_extra_fields(False)

    def get_simple_info_fields(self):
        if not self.simple_info_fields:
            self.simple_info_fields = [x.column for x in self._meta.local_fields if x.editable]
        return self.simple_info_fields + self.__class__.get_extra_fields()


    def _get_fields_data(self, fields):
        res = {}
        for field in fields:
            if hasattr(self, field):
                v = getattr(self, field)
                if hasattr(v, '__name__'):
                    field = v.__name__
                if callable(v):
                    v = v()
                res[field] = v

        res.update(self._get_cache_info())
        return res

    def _get_cache_info(self):
        res = {}
        for name in getattr(self._state, 'select_related', []):
            if name not in self.foreign_key_fields:
                continue

            obj = getattr(self, name)
            if not obj:
                continue
            obj._state.is_simple_info = getattr(self._state, 'is_simple_info', True)
            
            res[name] = obj.json_data()
        return res

    def full_info(self):
        return self._get_fields_data(self.get_full_info_fields())


    def simple_info(self):
        return self._get_fields_data(self.get_simple_info_fields())

    def simple(self):
        self._state.is_simple_info = True

    def full(self):
        self._state.is_simple_info = False

    def json_data(self):
        if getattr(self._state, 'is_simple_info', True):
            return self.simple_info()
        return self.full_info()


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
