#!/usr/bin/python
#coding=utf8
from django.contrib import admin
from django.core.exceptions import ValidationError
from .fields import MultiSelectField
from django.utils.encoding import smart_text



class UnixTimeIntervalFilter(admin.filters.FieldListFilter):
    parameter_name = 'date_interval'
    interval_format = {'hour' : "%%Y-%%m-%%d %%H", 'day' : "%%Y-%%m-%%d", 'minute' : "%%Y-%%m-%%d %%H:%%S", 'month' : "%%Y-%%m"}


    def queryset(self, request, queryset):
        v = self.used_parameters.get(self.parameter_name, 'hour')
        format = self.interval_format.get(v, self.interval_format['hour'])
        select_data = {self.field_path : 'DATE_FORMAT(from_unixtime(%s), "%s")' % (self.field_path, format)}
        try:
            return queryset.extra(select_data)
        except ValidationError as e:
            raise IncorrectLookupParameters(e)

    def expected_parameters(self):
        return [self.parameter_name]

    def value(self):
        """
        Returns the value (in string format) provided in the request's
        query string for this filter, if any. If the value wasn't provided then
        returns None.
        """
        return self.used_parameters.get(self.parameter_name, None)

    def choices(self, cl):
        for k in self.interval_format:
            yield {
                'selected': self.value() == k,
                'query_string': cl.get_query_string({
                    self.parameter_name: k,
                }, []),
                'display': k,
            }
       
class MultiSelectFieldListFilter(admin.filters.FieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = '%s__icontains' % field_path
        self.lookup_val = request.GET.get(self.lookup_kwarg)
        super(MultiSelectFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg]

    def choices(self, cl):
        yield {
            'selected': self.lookup_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display': '全部'
        }
        for lookup, title in self.field.flatchoices:
            lookup = '%s,' % lookup
            yield {
                'selected': smart_text(lookup) == self.lookup_val,
                'query_string': cl.get_query_string({
                                    self.lookup_kwarg: lookup}),
                'display': title,
            }

admin.filters.FieldListFilter.register(lambda f: isinstance(f, MultiSelectField), MultiSelectFieldListFilter, take_priority=9999)



