#!/usr/bin/python
#coding=utf8
from django.contrib import admin
from django.core.exceptions import ValidationError



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
       
