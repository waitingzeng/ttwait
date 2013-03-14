from django.contrib.admin.widgets import AdminFileWidget, AdminTextareaWidget, AdminURLFieldWidget
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.translation import ugettext as _
import urlparse


class AdminImageWidget(AdminFileWidget):
    """
    A FileField Widget that displays an image instead of a file path
    if the current file is an image.
    """
    def render(self, name, value, attrs=None):
        output = []

        file_name = str(value)

        if value and file_name:

            file_path = urlparse.urljoin(settings.MEDIA_URL, file_name)
            try:            # is image
                output.append('<a target="_blank" href="%(file_path)s"><img src="%(file_path)s" style="max-width:500px;max-height=300px" /></a> ' % locals())
            except IOError:  # not image
                output.append('%s <a target="_blank" href="%s">%s</a> <br />%s ' %
                             (_('Currently:'), file_path, file_name, _('Change:')))

        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))


class AdminImageURLFieldWidget(AdminURLFieldWidget):
    """
    A FileField Widget that displays an image instead of a file path
    if the current file is an image.
    """
    def render(self, name, value, attrs=None):
        output = []

        if value:
            value = urlparse.urljoin(settings.MEDIA_URL, value)

            output.append('<a target="_blank" href="%(value)s"><img src="%(value)s" style="max-width:500px;max-height=300px" /></a> <input type="hidden" name="%(name)s" value="%(value)s" />' % locals())
        else:
            output.append(super(AdminImageURLFieldWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))


class HTMLTextareaWidget(AdminTextareaWidget):
    class Media:
        extend = False
        js = ('js/tiny_mce/tiny_mce.js', 'js/tiny_mce_init.js',)
