"""JQuery-Ajax Autocomplete fields for Django Forms"""
__version__ = "1.2.5"
__author__ = "crucialfelix"
__contact__ = "crucialfelix@gmail.com"
__homepage__ = "https://github.com/crucialfelix/django-ajax-selects/"

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelForm
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _, ugettext


class LookupChannel(object):

    """Subclass this, setting model and overiding the methods below to taste"""

    model = None
    plugin_options = {}
    min_length = 1
    res_num = 10
    to_field = None
    ordering = None
    search_fields = []

    def get_query(self,q,request):
        """ return a query set searching for the query string q
            either implement this method yourself or set the search_field
            in the LookupChannel class definition
        """
        kwargs = {}
        print repr(q)
        for search_field in self.search_fields:
            kwargs = { "%s__icontains" % search_field : q.strip() }
        qs = self.model.objects.filter(**kwargs)
        if not self.ordering and self.search_fields:
            self.ordering = self.search_fields[0]
        if self.ordering:
            qs = qs.order_by(self.ordering)
        if self.res_num :
            qs = qs[:self.res_num]
        return qs

    def get_result(self,obj):
        """ The text result of autocompleting the entered query """
        return unicode(obj)

    def format_match(self,obj):
        """ (HTML) formatted item for displaying item in the dropdown """
        return unicode(obj)

    def format_item_display(self,obj):
        """ (HTML) formatted item for displaying item in the selected deck area """
        return unicode(obj)

    def get_objects(self,ids):
        """ Get the currently selected objects when editing an existing model """
        # return in the same order as passed in here
        # this will be however the related objects Manager returns them
        # which is not guaranteed to be the same order they were in when you last edited
        # see OrdredManyToMany.md
        if self.to_field is None:
            ids = [int(id) for id in ids]
            things = self.model.objects.in_bulk(ids)
            res = [things[aid] for aid in ids if things.has_key(aid)]
        else:
            things = {}
            values = ','.join("'%s'" % x for x in ids)
            where = '%s in (%s)' % (self.to_field, values)
            qs = self.model.objects.extra(where=[where])
            for item in qs:
                things[str(getattr(item, self.to_field))] = item
            res = [things[str(aid)] for aid in ids if things.has_key(str(aid))]
        return res


    def can_add(self,user,argmodel):
        """ Check if the user has permission to add
            one of these models. This enables the green popup +
            Default is the standard django permission check
        """
        ctype = ContentType.objects.get_for_model(argmodel)
        return user.has_perm("%s.add_%s" % (ctype.app_label,ctype.model))

    def check_auth(self,request):
        """ to ensure that nobody can get your data via json simply by knowing the URL.
            public facing forms should write a custom LookupChannel to implement as you wish.
            also you could choose to return HttpResponseForbidden("who are you?")
            instead of raising PermissionDenied (401 response)
         """
        if not request.user.is_staff:
            raise PermissionDenied



def make_ajax_form(model,fieldlist,superclass=ModelForm,show_help_text=False,**kwargs):
    """ Creates a ModelForm subclass with autocomplete fields

        usage:
            class YourModelAdmin(Admin):
                ...
                form = make_ajax_form(YourModel,{'contacts':'contact','author':'contact'})

        where
            'contacts' is a ManyToManyField specifying to use the lookup channel 'contact'
        and
            'author' is a ForeignKeyField specifying here to also use the lookup channel 'contact'
    """
    # will support previous arg name for several versions before deprecating
    if 'show_m2m_help' in kwargs:
        show_help_text = kwargs.pop('show_m2m_help')

    class TheForm(superclass):

        class Meta:
            pass
        setattr(Meta, 'model', model)

    for model_fieldname,channel in fieldlist.iteritems():
        f = make_ajax_field(model,model_fieldname,channel,show_help_text)

        TheForm.declared_fields[model_fieldname] = f
        TheForm.base_fields[model_fieldname] = f
        setattr(TheForm,model_fieldname,f)

    return TheForm


def make_ajax_field(model,model_fieldname,channel,show_help_text = False,**kwargs):
    """ Makes a single autocomplete field for use in a Form

        optional args:
            help_text - default is the model db field's help_text.
                None will disable all help text
            label     - default is the model db field's verbose name
            required  - default is the model db field's (not) blank

            show_help_text -
                Django will show help text below the widget, but not for ManyToMany inside of admin inlines
                This setting will show the help text inside the widget itself.
    """
    # will support previous arg name for several versions before deprecating
    if 'show_m2m_help' in kwargs:
        show_help_text = kwargs.pop('show_m2m_help')

    from .fields import AutoCompleteField, \
                                   AutoCompleteSelectMultipleField, \
                                   AutoCompleteSelectField

    field = model._meta.get_field(model_fieldname)
    if not kwargs.has_key('label'):
        kwargs['label'] = _(capfirst(unicode(field.verbose_name)))

    if not kwargs.has_key('help_text') and field.help_text:
        kwargs['help_text'] = field.help_text
    if not kwargs.has_key('required'):
        kwargs['required'] = not field.blank

    kwargs['show_help_text'] = show_help_text
    if isinstance(field,ManyToManyField):
        f = AutoCompleteSelectMultipleField(
            channel,
            **kwargs
            )
    elif isinstance(field,ForeignKey):
        f = AutoCompleteSelectField(
            channel,
            **kwargs
            )
    else:
        f = AutoCompleteField(
            channel,
            **kwargs
            )
    return f


####################  private  ##################################################

def get_lookup(channel):
    """ find the lookup class for the named channel.  this is used internally """
    try:
        lookup_label = settings.AJAX_LOOKUP_CHANNELS[channel]
    except AttributeError:
        raise ImproperlyConfigured("settings.AJAX_LOOKUP_CHANNELS is not configured")
    except KeyError:
        raise ImproperlyConfigured("settings.AJAX_LOOKUP_CHANNELS not configured correctly for %r" % channel)

    if isinstance(lookup_label,dict):
        # 'channel' : dict(model='app.model', search_field='title' )
        #  generate a simple channel dynamically
        return make_channel( lookup_label['model'], lookup_label['search_fields'], lookup_label.get('to_field', None) )
    else: # a tuple
        # 'channel' : ('app.module','LookupClass')
        #  from app.module load LookupClass and instantiate
        lookup_module = __import__( lookup_label[0],{},{},[''])
        lookup_class = getattr(lookup_module,lookup_label[1] )

        # monkeypatch older lookup classes till 1.3
        if not hasattr(lookup_class,'format_match'):
            setattr(lookup_class, 'format_match',
                getattr(lookup_class,'format_item',
                    lambda self,obj: unicode(obj)))
        if not hasattr(lookup_class,'format_item_display'):
            setattr(lookup_class, 'format_item_display',
                getattr(lookup_class,'format_item',
                    lambda self,obj: unicode(obj)))
        if not hasattr(lookup_class,'get_result'):
            setattr(lookup_class, 'get_result',
                getattr(lookup_class,'format_result',
                    lambda self,obj: unicode(obj)))

        return lookup_class()


def make_channel(app_model, arg_search_fields, target_field=None):
    """ used in get_lookup
            app_model :   app_name.model_name
            search_field :  the field to search against and to display in search results
    """
    from django.db import models
    app_label, model_name = app_model.split(".")
    themodel = models.get_model(app_label, model_name)
    if not isinstance(arg_search_fields, (tuple, list)):
        arg_search_fields = [arg_search_fields]

    class MadeLookupChannel(LookupChannel):
        model = themodel
        to_field = target_field

        search_fields = arg_search_fields
    
    return MadeLookupChannel()


