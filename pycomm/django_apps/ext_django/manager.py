#!/usr/bin/python
#coding=utf8
from django.db import models
from django.db.models.query import QuerySet, EmptyQuerySet, RawQuerySet
from pycomm.utils.storage import Storage
from django.db import connections


class CustomBase(object):
    def simple(self):
        self.is_simple_info = True
        return self

    def full(self):
        self.is_simple_info = False
        return self

    def iterator(self):
        for item in super(self.__class__, self).iterator():
            if getattr(self, 'is_simple_info', True):
                item.simple()
            else:
                item.full()
            yield item

    def json_data(self):
        return [x.json_data() for x in self]


class CustomQuerySet(QuerySet):

    def in_bulk_order(self, ids, *args, **kwargs):
        result = self.in_bulk(ids, *args, **kwargs)
        res = []

        for id in ids:
            res.append(result.get(id, None))
        return res

    def simple(self):
        self.is_simple_info = True
        return self

    def full(self):
        self.is_simple_info = False
        return self

    def iterator(self):
        for item in super(self.__class__, self).iterator():
            item._state.select_related = self.query.select_related and isinstance(self.query.select_related, (list, tuple)) \
                and self.query.select_related[:] or []
            if getattr(self, 'is_simple_info', True):
                item.simple()
            else:
                item.full()
            yield item

    def json_data(self):
        return [x.json_data() for x in self]

    def _clone(self, *args, **kwargs):
        obj = super(self.__class__, self)._clone(*args, **kwargs)
        obj.is_simple_info = getattr(self, 'is_simple_info', True)
        return obj

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except:
            import traceback
            traceback.print_exc(10)
            return None

    def get_first(self, *args, **kwargs):
        objs = list(self.filter(*args, **kwargs)[:1])
        if not objs:
            return None
        return objs[0]

class CustomRawQuerySet(RawQuerySet, CustomBase):

    def simple(self):
        self.is_simple_info = True
        return self

    def full(self):
        self.is_simple_info = False
        return self

    def iterator(self):
        for item in super(self.__class__, self).iterator():
            if getattr(self, 'is_simple_info', True):
                item.simple()
            else:
                item.full()
            yield item

    def json_data(self):
        return [x.json_data() for x in self]

    def _clone(self, *args, **kwargs):
        obj = super(self.__class__, self)._clone(*args, **kwargs)
        obj.is_simple_info = getattr(self, 'is_simple_info', True)
        return obj


class ModelManager(models.Manager):
    def in_bulk_order(self, *args, **kwargs):
        return self.get_query_set().in_bulk_order(*args, **kwargs)

    def get_query_set(self):
        return CustomQuerySet(self.model, using=self._db)

    def raw(self, raw_query, params=None, *args, **kwargs):
        return CustomRawQuerySet(raw_query=raw_query, model=self.model, params=params, using=self._db, *args, **kwargs)

    def simple(self):
        return self.get_query_set().simple()

    def full(self):
        return self.get_query_set().full()

    def get_conn(self):
        return connections[self.db]

    def execute(self, sql, *args, **kwargs):
        cursor = self.get_conn().cursor()
        cursor.execute(sql, *args, **kwargs)

        return cursor

    def fetchall(self, sql, *args, **kwargs):
        cursor = self.execute(sql, *args, **kwargs)
        return cursor.fetchall()

    def fetchone(self, sql, *args, **kwargs):
        cursor = self.execute(sql)
        return cursor.fetchone()

    def dictfetchall(self, sql, *args, **kwargs):
        "Returns all rows from a cursor as a dict"
        cursor = self.execute(sql, *args, **kwargs)
        desc = cursor.description
        return [
            Storage(dict(zip([col[0] for col in desc], row)))
            for row in cursor.fetchall()
        ]

    def get_all_fields_name(self):
        return [x.name for x in self.model._meta.fields if x.editable and not isinstance(x, models.ForeignKey)]

    def get_or_none(self, **kwargs):
        return self.get_query_set().get_or_none(**kwargs)

    def get_first(self, *args, **kwargs):
        return self.get_query_set().get_first()

def main():
    from mfhui_admin.reviews.models import Reviews

    qs = Reviews.objects.full()
    print qs.is_simple_info
    new_qs = qs.filter(goods_id__gt=0)
    print new_qs.is_simple_info

if __name__ == '__main__':
    main()


