from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.translation import ugettext as _
try:
    from PIL import Image
except:
    pass
import os

class AdminImageWidget(AdminFileWidget):
    """
    A FileField Widget that displays an image instead of a file path
    if the current file is an image.
    """
    def render(self, name, value, attrs=None):
        output = []

        file_name = str(value)

        if value and file_name:
            file_path = '%s%s' % (settings.MEDIA_URL, file_name)
            try:            # is image
                output.append('<a target="_blank" href="%(file_path)s"><img src="%(file_path)s" width="100px" /></a> ' % locals())
            except IOError: # not image
                output.append('%s <a target="_blank" href="%s">%s</a> <br />%s ' % \
                    (_('Currently:'), file_path, file_name, _('Change:')))
            
        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))
