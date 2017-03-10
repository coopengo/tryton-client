import gtk

from .widget import Widget
from .binary import BinaryMixin


class Icon(BinaryMixin, Widget):
    """
        Coopengo Specific. This widget displays a 'Char' field as the name of
        an icon and also allows us to modify the icon dynamically.
        https://redmine.coopengo.com/issues/2245
    """

    def __init__(self, view, attrs):
        super(Icon, self).__init__(view, attrs)
        self.height = int(attrs.get('height', 60))
        self.width = int(attrs.get('width', 60))
        size_name = str(self.width) + '_' + str(self.height)
        self.size = gtk.icon_size_from_name(size_name)
        if self.size.numerator == 0:
            self.size = gtk.icon_size_register(size_name, self.width,
                self.height)
        self.widget = gtk.Image()
        self.update_icon()

    def update_icon(self):
        if not self.field:
            return
        icon_name = self.field.get_client(self.record)
        pixbuf = self.widget.render_icon(icon_name, self.size)
        self.widget.set_from_pixbuf(pixbuf)

    def display(self, record, field):
        super(Icon, self).display(record, field)
        self.update_icon()
