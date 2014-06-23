import json
import gettext
import _ast
from pyflakes.checker import Checker
import pyflakes.messages

import gobject
import gtk
import pango
import gtksourceview2 as gtksourceview

from .widget import Widget

_ = gettext.gettext
CODE_TEMPLATE = """
from decimal import Decimal
Decimal(0)

def test():
%s
"""

WARNING = 'lightblue'
ERROR = 'red'
SYNTAX = 'darkred'

MARKS = {
    SYNTAX: (3, 'tryton-dialog-error'),
    ERROR: (2, 'tryton-dialog-warning'),
    WARNING: (1, 'tryton-dialog-information'),
    }

ERROR2COLOR = {
    }
for name, type_ in (
        ('UnusedImport', WARNING),
        ('Redefined', WARNING),
        ('RedefinedInListComp', WARNING),
        ('RedefinedWhileUnused', WARNING),
        ('ImportShadowedByLoopVar', WARNING),
        ('ImportStarUsed', WARNING),
        ('UndefinedExport', WARNING),
        ('RedefinedFunction', WARNING),
        ('LateFutureImport', WARNING),
        ('UnusedVariable', WARNING),
        ('UndefinedName', ERROR),
        ('UndefinedLocal', ERROR),
        ('DuplicateArgument', ERROR),
        ('Message', SYNTAX),
        ):
    message = getattr(pyflakes.messages, name, None)
    if message is not None:
        ERROR2COLOR[message] = type_


def check_code(code):
    try:
        tree = compile(code, 'test', 'exec', _ast.PyCF_ONLY_AST)
    except SyntaxError, syn_error:
        error = pyflakes.messages.Message('test', syn_error)
        error.message = 'Syntax Error'
        return [error]
    else:
        warnings = Checker(tree, 'test')
        return warnings.messages


class SourceView(Widget):
    expand = True

    def __init__(self, view, attrs):
        super(SourceView, self).__init__(view, attrs)

        vbox = gtk.VBox(homogeneous=False, spacing=2)
        sc_editor = gtk.ScrolledWindow()
        sc_editor.set_policy(gtk.POLICY_AUTOMATIC,
            gtk.POLICY_AUTOMATIC)
        sc_editor.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sc_editor.set_size_request(-1, 80)

        language_manager = gtksourceview.language_manager_get_default()
        python = language_manager.get_language('python')
        self.sourcebuffer = gtksourceview.Buffer(language=python)
        self.sourcebuffer.connect('changed', self._clear_marks)

        self.sourceview = gtksourceview.View(self.sourcebuffer)
        self.sourceview.connect('focus-out-event', lambda x, y:
            self._focus_out())
        self.sourceview.connect('key-press-event', self.send_modified)
        self.sourceview.connect('key-press-event', self._test_check)
        self.sourceview.set_insert_spaces_instead_of_tabs(True)
        self.sourceview.set_tab_width(4)
        self.sourceview.set_auto_indent(True)
        self.sourceview.set_show_line_numbers(True)
        self.sourceview.set_show_line_marks(True)

        tag_table = self.sourcebuffer.get_tag_table()
        for mark_type, (priority, stock_id) in MARKS.items():
            self.sourceview.set_mark_category_icon_from_stock(mark_type,
                stock_id)
            self.sourceview.set_mark_category_priority(mark_type, priority)
            tag = gtk.TextTag(name=mark_type)
            if mark_type in (ERROR, SYNTAX):
                tag.props.underline = pango.UNDERLINE_ERROR
                tag.props.underline_set = True
            tag_table.add(tag)

        mono_desc = pango.FontDescription('monospace')
        if mono_desc:
            self.sourceview.modify_font(mono_desc)

        sc_editor.add(self.sourceview)

        toolbar = gtk.Toolbar()
        undo_btn = gtk.ToolButton('gtk-undo')
        undo_btn.connect('clicked', self.undo)
        toolbar.insert(undo_btn, -1)
        redo_btn = gtk.ToolButton('gtk-redo')
        redo_btn.connect('clicked', self.redo)
        toolbar.insert(redo_btn, -1)
        #check_btn = gtk.ToolButton(label='Check Code')
        check_btn = gtk.ToolButton('gtk-apply')
        check_btn.connect('clicked', self.check_code)
        toolbar.insert(check_btn, -1)

        self.error_store = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING,
            gobject.TYPE_STRING)

        error_list = gtk.TreeView(self.error_store)
        error_list.set_enable_search(False)
        line_col = gtk.TreeViewColumn(_('L'))
        renderer = gtk.CellRendererText()
        line_col.pack_start(renderer, True)
        line_col.add_attribute(renderer, 'text', 0)
        line_col.add_attribute(renderer, 'cell-background', 2)
        error_list.append_column(line_col)
        error_col = gtk.TreeViewColumn(_('Message'))
        renderer = gtk.CellRendererText()
        error_col.pack_start(renderer, True)
        error_col.add_attribute(renderer, 'text', 1)
        error_col.add_attribute(renderer, 'cell-background', 2)
        error_list.append_column(error_col)
        sc_error = gtk.ScrolledWindow()
        sc_error.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        sc_error.add_with_viewport(error_list)
        self.error_tree = sc_error

        error_selection = error_list.get_selection()
        error_selection.connect_after('changed', self.focus_line)

        vbox.pack_start(toolbar, expand=False, fill=True)
        vbox.pack_start(sc_editor, expand=True, fill=True)
        vbox.pack_start(sc_error, expand=True, fill=True)
        vbox.show_all()

        self.tree_data_field = attrs.get('context_tree')
        if self.tree_data_field:
            sc_tree = gtk.ScrolledWindow()
            sc_tree.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sc_tree.set_shadow_type(gtk.SHADOW_ETCHED_IN)
            sc_tree.set_size_request(-1, 30)

            self.model = gtk.TreeStore(gobject.TYPE_PYOBJECT,
                gobject.TYPE_STRING)
            self.treeview = gtk.TreeView(self.model)
            self.treeview.set_headers_visible(False)
            self.treeview.set_tooltip_column(1)
            self.treeview.connect('query-tooltip', self.tree_display_tooltip)
            tree_cell = gtk.CellRendererText()
            tree_col = gtk.TreeViewColumn('Objects')
            tree_col.pack_start(tree_cell)

            def cell_setter(column, cell, store, iter):
                if not self.treeview.get_realized():
                    return
                record = store.get_value(iter, 0)
                cell.set_property('text', record['description'])
            tree_col.set_cell_data_func(tree_cell, cell_setter)
            self.treeview.append_column(tree_col)
            self.treeview.drag_source_set(gtk.gdk.BUTTON1_MASK,
                [('TREE_ROW', gtk.TARGET_SAME_APP, 0)],
                gtk.gdk.ACTION_COPY)
            self.sourceview.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                [('TREE_ROW', gtk.TARGET_SAME_APP, 0)],
                gtk.gdk.ACTION_COPY)
            self.treeview.connect('drag-data-get', self.drag_data_get)
            self.sourceview.connect('drag-data-received',
                self.drag_data_received_data)
            self.sourceview.connect('drag-drop', self.drag_drop)
            self.treeview.show_all()
            sc_tree.add(self.treeview)

            self.widget = gtk.HPaned()
            self.widget.pack1(sc_tree)
            self.widget.pack2(vbox)
            self.widget.set_position(250)
        else:
            self.widget = vbox

        self.tree_data = []
        self.known_funcs = set()

    def grab_focus(self):
        return self.sourceview.grab_focus()

    def _readonly_set(self, value):
        pass

    def _color_widget(self):
        return self.sourceview

    @property
    def modified(self):
        if self.record and self.field:
            return self.field.get_client(self.record) != self.get_value()
        return False

    def get_value(self):
        iter_start = self.sourcebuffer.get_start_iter()
        iter_end = self.sourcebuffer.get_end_iter()
        return self.sourcebuffer.get_text(iter_start, iter_end, False)

    def set_value(self, record, field):
        field.set_client(record, self.get_value())

    def display(self, record, field):
        super(SourceView, self).display(record, field)
        value = field and field.get_client(record)
        if not value:
            value = ''

        if self.get_value() != value:
            self.sourcebuffer.begin_not_undoable_action()
            self.sourcebuffer.set_text(value)
            self.sourcebuffer.end_not_undoable_action()
            begin, end = self.sourcebuffer.get_bounds()
            self.sourcebuffer.remove_source_marks(begin, end)
            self.error_store.clear()

        if self.tree_data_field:
            if not record:
                return
            tree_field = record[self.tree_data_field]
            json_data = tree_field.get(record)
            if json_data:
                tree_data = json.loads(json_data)
                if self.tree_data != tree_data:
                    self.model.clear()
                    self.known_funcs.clear()
                    self.tree_data = tree_data
                    self.populate_tree(self.tree_data)
            else:
                self.tree_data = []
                self.model.clear()
                self.known_funcs.clear()
        self.check_code()

    def populate_tree(self, tree_data, parent=None):
        for element in tree_data:
            if element['type'] != 'folder':
                self.known_funcs.add(element['translated'])
            if element['long_description']:
                desc = element['long_description']
            else:
                desc = ''
            if element['fct_args']:
                param_txt = _('Parameters: {}').format(element['fct_args'])
            else:
                param_txt = _('No parameters')
            if desc:
                good_text = desc + '\n' * 2 + param_txt
            else:
                good_text = param_txt
            new_iter = self.model.append(parent, [element, good_text])
            self.populate_tree(element['children'], new_iter)

    def drag_data_get(self, treeview, context, selection, target_id, etime):
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        if iter:
            func_text = '{translated}({fct_args})'.format(**model[iter][0])
            selection.set(selection.target, 8, func_text)

    def drag_data_received_data(self, sourceview, context, x, y, selection,
            info, etime):
        buff_x, buff_y = sourceview.window_to_buffer_coords(
            gtk.TEXT_WINDOW_WIDGET, x, y)
        iter = sourceview.get_iter_at_location(buff_x, buff_y)
        self.sourcebuffer.insert(iter, selection.data)
        context.finish(True, True, etime)
        sourceview.grab_focus()

    def drag_drop(self, sourceview, context, x, y, etime):
        return True

    def undo(self, button):
        if self.sourcebuffer.can_undo():
            self.sourcebuffer.undo()

    def redo(self, button):
        if self.sourcebuffer.can_redo():
            self.sourcebuffer.redo()

    def get_code(self):
        begin, end = self.sourcebuffer.get_bounds()
        code = self.sourcebuffer.get_text(begin, end, False)
        return CODE_TEMPLATE % '\n'.join(' ' + l for l in code.splitlines())

    def check_code(self, button=None):
        self.error_store.clear()
        begin, end = self.sourcebuffer.get_bounds()
        tag_table = self.sourcebuffer.get_tag_table()
        self.sourcebuffer.remove_source_marks(begin, end)
        for tagname in ERROR2COLOR.values():
            tag = tag_table.lookup(tagname)
            self.sourcebuffer.remove_tag(tag, begin, end)
        errors = check_code(self.get_code())
        has_errors = False
        for idx, message in enumerate(errors):
            if (isinstance(message, pyflakes.messages.UndefinedName)
                    and message.message_args[0] in self.known_funcs):
                continue
            error_type = ERROR2COLOR.get(message.__class__, SYNTAX)
            # "5" is the number of lines of the template before the actual
            # code
            has_errors = True
            line_nbr = message.lineno - 5
            self.error_store.append((line_nbr,
                    message.message % message.message_args, error_type))
            line = self.sourcebuffer.props.text.split('\n')[line_nbr -
                1].decode('utf-8')
            line_start = self.sourcebuffer.get_iter_at_line_offset(
                line_nbr - 1, 0)
            line_end = self.sourcebuffer.get_iter_at_line_offset(
                line_nbr - 1, len(line))
            self.sourcebuffer.create_source_mark(str(idx), error_type,
                line_start)
            tag = tag_table.lookup(error_type)
            self.sourcebuffer.apply_tag(tag, line_start, line_end)
        self.error_tree.set_visible(has_errors)

    def focus_line(self, selection):
        model, tree_iter = selection.get_selected()
        if not tree_iter:
            return
        lineno = self.error_store[tree_iter][0]
        line = self.sourcebuffer.props.text.split('\n')[lineno - 1]
        textiter = self.sourcebuffer.get_iter_at_line_offset(lineno - 1,
            len(line))
        self.sourceview.scroll_to_iter(textiter, within_margin=0.,
            use_align=True)
        self.sourcebuffer.place_cursor(textiter)
        gobject.idle_add(self.sourceview.grab_focus)

    def _test_check(self, sourceview, event):
        if gtk.gdk.keyval_name(event.keyval) == 'F7':
            self.check_code(None)
            sourceview.emit_stop_by_name('key-press-event')

    def _clear_marks(self, sourcebuffer):
        tag_table = sourcebuffer.get_tag_table()
        iters = []
        insert_mark = sourcebuffer.get_insert()
        if insert_mark:
            iters.append(sourcebuffer.get_iter_at_mark(insert_mark))
        if sourcebuffer.get_has_selection():
            iters.extend(list(sourcebuffer.get_selection_bounds()))
        for iter_ in iters:
            line = iter_.get_line()
            chars = iter_.get_chars_in_line()
            if chars > 0:
                chars -= 1
            start = sourcebuffer.get_iter_at_line_offset(line, 0)
            end = sourcebuffer.get_iter_at_line_offset(line, chars)
            for error_type in MARKS.keys():
                sourcebuffer.remove_source_marks(start, end, error_type)
                tag = tag_table.lookup(error_type)
                sourcebuffer.remove_tag(tag, start, end)

    def tree_display_tooltip(self, treeview, x, y, keyboard_mode, tooltip):
        return False
