#!/usr/bin/python
#coding=utf8

from pycomm.django_apps.ext_django import admin
import models


class CategoryAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_select_related = False
    list_display = [u'id', 'name', 'display_order', 'img']
    search_fields = ['name', 'parent_path', 'img']
    list_filter = ['create_time', 'update_time']
    list_editable = []
    date_hierarchy = None
    raw_id_fields = ['parent']
    autocomplete_lookup_fields = {'m2m': [], 'fk': ['parent']}

admin.site.register(models.Category, CategoryAdmin)


class GoodsAttrAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_select_related = False
    list_display = [u'id', 'name', 'display_order']
    search_fields = ['name', 'parent_path']
    list_filter = ['create_time', 'update_time']
    list_editable = []
    date_hierarchy = None
    raw_id_fields = ['parent']
    autocomplete_lookup_fields = {'m2m': [], 'fk': ['parent']}

admin.site.register(models.GoodsAttr, GoodsAttrAdmin)


class GoodsImgAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_select_related = False
    list_display = [u'id', 'path']
    search_fields = ['path']
    list_filter = []
    list_editable = []
    date_hierarchy = None
    raw_id_fields = ['goods_info']
    autocomplete_lookup_fields = {'m2m': [], 'fk': ['goods_info']}

admin.site.register(models.GoodsImg, GoodsImgAdmin)


class GoodsInfoAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_select_related = False
    list_display = [u'id', 'name', 'price', 'detail', 'design_data', 'can_addcart']
    search_fields = ['name', 'detail', 'design_data']
    list_filter = ['can_addcart']
    list_editable = ['can_addcart']
    date_hierarchy = None
    raw_id_fields = ['category', 'tags', 'attrs']
    autocomplete_lookup_fields = {'m2m': ['tags', 'attrs'], 'fk': ['category']}

admin.site.register(models.GoodsInfo, GoodsInfoAdmin)


class GoodsInfoAttrAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_select_related = False
    list_display = [u'id', 'value', 'extra']
    search_fields = ['value', 'extra']
    list_filter = []
    list_editable = []
    date_hierarchy = None
    raw_id_fields = ['attr', 'goods_info']
    autocomplete_lookup_fields = {'m2m': [], 'fk': ['attr', 'goods_info']}

admin.site.register(models.GoodsInfoAttr, GoodsInfoAttrAdmin)


class TagsAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_select_related = False
    list_display = [u'id', 'name', 'display_order']
    search_fields = ['name', 'parent_path']
    list_filter = ['create_time', 'update_time']
    list_editable = []
    date_hierarchy = None
    raw_id_fields = ['parent']
    autocomplete_lookup_fields = {'m2m': [], 'fk': ['parent']}

admin.site.register(models.Tags, TagsAdmin)



from pycomm.django_apps.ext_django.admin import auto_admin_for_models

auto_admin_for_models(models)
