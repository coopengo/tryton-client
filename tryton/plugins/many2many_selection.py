import gtk
import gobject

from tryton.gui.window.view_form.view.form import ViewForm
from tryton.gui.window.view_form.view.form_gtk.widget import Widget
from tryton.gui.window.view_form.screen import Screen
from tryton.common.selection import SelectionMixin
from tryton.common.treeviewcontrol import MOVEMENT_KEYS


def get_plugins(model):
    return []


class Many2ManySelection(Widget, SelectionMixin):
    expand = True

    def __init__(self, view, attrs):
        super(Many2ManySelection, self).__init__(view, attrs)

        self.widget = gtk.VBox(homogeneous=False, spacing=5)

        hbox = gtk.HBox(homogeneous=False, spacing=0)
        hbox.set_border_width(2)

        label = gtk.Label(attrs.get('string', ''))
        label.set_alignment(0.0, 0.5)
        hbox.pack_start(label, expand=True, fill=True)

        frame = gtk.Frame()
        frame.add(hbox)
        frame.set_shadow_type(gtk.SHADOW_OUT)
        self.widget.pack_start(frame, expand=False, fill=True)

        self.screen = Screen(attrs['relation'],
            view_ids=attrs.get('view_ids', '').split(','),
            mode=['tree'], views_preload=attrs.get('views', {}))
        self.screen.new_group()
        self.treeview = self.screen.current_view.treeview
        self.treeview.get_selection().connect('changed', self.changed)
        self.treeview.connect('focus-out-event', lambda *a: self._focus_out())

        self.treeview.connect('button-press-event', self.button_press_event)
        self.treeview.connect('key-press-event', self.key_press_event)

        self.widget.pack_start(self.screen.widget, expand=True, fill=True)

        self.nullable_widget = False
        self.init_selection()

    @property
    def modified(self):
        if self.record and self.field:
            group = set(r.id for r in self.field.get_client(self.record))
            value = set(self.get_value())
            return value != group
        return False

    def changed(self, selection):
        def focus_out():
            if self.widget.props.window:
                self._focus_out()
        # Must be deferred because it triggers a display of the form
        gobject.idle_add(focus_out)

    def button_press_event(self, treeview, event):
        # grab focus because it doesn't whith CONTROL MASK
        treeview.grab_focus()
        if event.button == 1:
            event.state ^= gtk.gdk.CONTROL_MASK

    def key_press_event(self, treeview, event):
        if event.keyval in MOVEMENT_KEYS:
            event.state ^= gtk.gdk.CONTROL_MASK

    def get_value(self):
        return [r.id for r in self.screen.selected_records]

    def set_value(self, record, field):
        field.set_client(record, self.get_value())

    def display(self, record, field):
        selection = self.treeview.get_selection()
        selection.handler_block_by_func(self.changed)
        try:
            self.update_selection(record, field)
            super(Many2ManySelection, self).display(record, field)
            if field is None:
                self.screen.clear()
                self.screen.current_record = None
                self.screen.parent = None
            else:
                self.screen.parent = record
                current_ids = [r.id for r in self.screen.group]
                new_ids = [s[0] for s in self.selection]
                if current_ids != new_ids:
                    self.screen.clear()
                    self.screen.load(new_ids)
                group = field.get_client(record)
                nodes = [[r.id] for r in group
                    if r not in group.record_removed
                    and r not in group.record_deleted]
                selection.unselect_all()
                self.screen.current_view.select_nodes(nodes)
            self.screen.display()
        finally:
            selection.handler_unblock_by_func(self.changed)

ViewForm.WIDGETS['many2many_selection'] = Many2ManySelection
