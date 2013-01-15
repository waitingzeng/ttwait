from .widgets import ChainedSelect, ChainedMultipleSelect, ChainedFilteredSelectMultiple
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from django.forms import ChoiceField
from django.db.models import get_model
from django.contrib.admin.widgets import FilteredSelectMultiple


class ChainedModelChoiceField(ModelChoiceField):
    def __init__(self, app_name, model_name, chain_field, model_field, show_all, auto_choose, manager=None, initial=None, *args, **kwargs):
        limit_choices_to = kwargs.pop('limit_choices_to', {})
        default_widget = kwargs.pop('widget', None)

        self.verbose_name = kwargs.pop('verbose_name', None)
        self.is_stacked = kwargs.pop('is_stacked', None)

        defaults = {
            'widget': ChainedSelect(app_name, model_name, chain_field, model_field, show_all, auto_choose, manager, limit_choices_to=limit_choices_to),
        }
        defaults.update(kwargs)
        if not 'queryset' in kwargs:
            queryset = get_model(app_name, model_name).objects.all()
            ModelChoiceField.__init__(self, queryset=queryset, initial=initial, *args, **defaults)
        else:
            ModelChoiceField.__init__(self, initial=initial, *args, **defaults)

    def _get_choices(self):
        ChainedSelect.queryset = self.queryset
        choices = ModelChoiceField._get_choices(self)
        return choices
    choices = property(_get_choices, ChoiceField._set_choices)

class ChainedModelMultipleChoiceField(ModelMultipleChoiceField):
    def __init__(self, app_name, model_name, chain_field, model_field, show_all, auto_choose, manager=None, initial=None, *args, **kwargs):
        limit_choices_to = kwargs.pop('limit_choices_to', {})
        default_widget = kwargs.pop('widget', None)

        if default_widget and isinstance(default_widget, FilteredSelectMultiple):
            widget = ChainedFilteredSelectMultiple(app_name, model_name, chain_field, model_field, show_all, auto_choose, manager, limit_choices_to=limit_choices_to, verbose_name=default_widget.verbose_name, is_stacked=default_widget.is_stacked)
        else:
            widget = ChainedMultipleSelect(app_name, model_name, chain_field, model_field, show_all, auto_choose, manager, limit_choices_to=limit_choices_to)

        defaults = {
            'widget': widget
        }
        defaults.update(kwargs)
        if not 'queryset' in kwargs:
            queryset = get_model(app_name, model_name).objects.all()
            ModelMultipleChoiceField.__init__(self, queryset=queryset, initial=initial, *args, **defaults)
        else:
            ModelMultipleChoiceField.__init__(self, initial=initial, *args, **defaults)

    def _get_choices(self):
        ChainedMultipleSelect.queryset = self.queryset
        choices = ModelMultipleChoiceField._get_choices(self)
        return choices
    choices = property(_get_choices, ChoiceField._set_choices)


class GroupedModelSelect(ModelChoiceField):
    def __init__(self, queryset, order_field, *args, **kwargs):
        self.order_field = order_field
        super(GroupedModelSelect, self).__init__(queryset, *args, **kwargs)

    def _get_choices(self):
        # If self._choices is set, then somebody must have manually set
        # the property self.choices. In this case, just return self._choices.
        if hasattr(self, '_choices'):
            return self._choices
        # Otherwise, execute the QuerySet in self.queryset to determine the
        # choices dynamically. Return a fresh QuerySetIterator that has not been
        # consumed. Note that we're instantiating a new QuerySetIterator *each*
        # time _get_choices() is called (and, thus, each time self.choices is
        # accessed) so that we can ensure the QuerySet has not been consumed. This
        # construct might look complicated but it allows for lazy evaluation of
        # the queryset.
        final = [("", self.empty_label or "---------"), ]
        group = None
        for item in self.queryset:
            if not group or group[0] != unicode(getattr(item, self.order_field)):
                if group:
                    final.append(group)
                group = [unicode(getattr(item, self.order_field)), []]
            group[1].append(self.make_choice(item))
        return final

    def make_choice(self, obj):
        return (obj.pk, "   " + self.label_from_instance(obj))

    choices = property(_get_choices, ChoiceField._set_choices)



