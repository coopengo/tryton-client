import gettext
import json
import os.path
import sys

import _ast
import pyflakes.messages
from gi.repository import Gdk, GLib, GObject, Gtk, GtkSource, Pango
from pyflakes.checker import Checker

from .widget import Widget

_ = gettext.gettext
# For each imported module, we need to use it once, to prevent
# 'imported but no used' error to be displayed
CODE_TEMPLATE = """
from decimal import Decimal
import datetime
from dateutil.relativedelta import relativedelta
Decimal(0)
datetime.date(2000, 1, 1)
relativedelta()

def test():
%s
"""

WARNING = 'lightblue'
ERROR = 'red'
SYNTAX = 'darkred'

MARKS = {
    SYNTAX: (3, 'tryton-dialog-error'),
    ERROR: (2, 'tryton-warning'),
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

LANG_PATH = None
if sys.platform == 'win32':
    if getattr(sys, 'frozen', False):
        datadir = os.path.dirname(sys.executable)
        LANG_PATH = [os.path.join(datadir, 'share')]


def check_code(code):
    try:
        tree = compile(code, 'test', 'exec', _ast.PyCF_ONLY_AST)
    except SyntaxError as syn_error:
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

        vbox = Gtk.VBox(homogeneous=False, spacing=2)
        sc_editor = Gtk.ScrolledWindow()
        sc_editor.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sc_editor.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sc_editor.set_size_request(-1, 80)

        style_scheme_manager = GtkSource.StyleSchemeManager.get_default()
        language_manager = GtkSource.LanguageManager.get_default()
        if LANG_PATH is not None:
            style_scheme_manager.prepend_search_path(LANG_PATH[0])
            language_manager.set_search_path(LANG_PATH)
        python = language_manager.get_language('python3')
        self.sourcebuffer = GtkSource.Buffer(language=python)
        self.sourcebuffer.connect('changed', self._clear_marks)

        self.sourceview = GtkSource.View.new_with_buffer(self.sourcebuffer)
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
        for mark_type, (priority, stock_id) in list(MARKS.items()):
            mark_attrs = GtkSource.MarkAttributes()
            mark_attrs.set_icon_name(stock_id)
            self.sourceview.set_mark_attributes(mark_type,
                mark_attrs, priority)
            tag = Gtk.TextTag(name=mark_type)
            if mark_type in (ERROR, SYNTAX):
                tag.props.underline = Pango.Underline.ERROR
                tag.props.underline_set = True
            tag_table.add(tag)

        mono_desc = Pango.FontDescription('monospace')
        if mono_desc:
            self.sourceview.modify_font(mono_desc)

        sc_editor.add(self.sourceview)

        toolbar = Gtk.Toolbar()
        undo_btn = Gtk.ToolButton('gtk-undo')
        undo_btn.connect('clicked', self.undo)
        toolbar.insert(undo_btn, -1)
        redo_btn = Gtk.ToolButton('gtk-redo')
        redo_btn.connect('clicked', self.redo)
        toolbar.insert(redo_btn, -1)
        check_btn = Gtk.ToolButton('gtk-apply')
        check_btn.connect('clicked', self.check_code)
        toolbar.insert(check_btn, -1)

        self.error_store = Gtk.ListStore(
            GObject.TYPE_INT, GObject.TYPE_STRING, GObject.TYPE_STRING)

        error_list = Gtk.TreeView(self.error_store)
        error_list.set_enable_search(False)
        line_col = Gtk.TreeViewColumn(_('L'))
        renderer = Gtk.CellRendererText()
        line_col.pack_start(renderer, True)
        line_col.add_attribute(renderer, 'text', 0)
        line_col.add_attribute(renderer, 'cell-background', 2)
        error_list.append_column(line_col)
        error_col = Gtk.TreeViewColumn(_('Message'))
        renderer = Gtk.CellRendererText()
        error_col.pack_start(renderer, True)
        error_col.add_attribute(renderer, 'text', 1)
        error_col.add_attribute(renderer, 'cell-background', 2)
        error_list.append_column(error_col)
        sc_error = Gtk.ScrolledWindow()
        sc_error.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc_error.add_with_viewport(error_list)
        self.error_tree = sc_error

        error_selection = error_list.get_selection()
        error_selection.connect_after('changed', self.focus_line)

        vbox.pack_start(toolbar, expand=False, fill=True, padding=0)
        vbox.pack_start(sc_editor, expand=True, fill=True, padding=0)
        vbox.pack_start(sc_error, expand=True, fill=True, padding=0)
        vbox.show_all()

        self.tree_data_field = attrs.get('context_tree')
        if self.tree_data_field:
            sc_tree = Gtk.ScrolledWindow()
            sc_tree.set_policy(
                Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            sc_tree.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
            sc_tree.set_size_request(-1, 30)

            self.model = Gtk.TreeStore(
                GObject.TYPE_PYOBJECT, GObject.TYPE_STRING)
            self.treeview = Gtk.TreeView(self.model)
            self.treeview.set_headers_visible(False)
            self.treeview.set_tooltip_column(1)
            self.treeview.connect('query-tooltip', self.tree_display_tooltip)
            tree_cell = Gtk.CellRendererText()
            tree_col = Gtk.TreeViewColumn('Objects')
            tree_col.pack_start(tree_cell, True)

            def cell_setter(column, cell, store, iter, data):
                if not self.treeview.get_realized():
                    return
                record = store.get_value(iter, 0)
                cell.set_property('text', record['description'])
            tree_col.set_cell_data_func(tree_cell, cell_setter)
            self.treeview.append_column(tree_col)

            target_entry = Gtk.TargetEntry(
                'TREE_ROW', Gtk.TargetFlags.SAME_APP, 0)

            self.treeview.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                [target_entry], Gdk.DragAction.COPY)
            self.sourceview.drag_dest_set(
                Gtk.DestDefaults.ALL, [target_entry], Gdk.DragAction.COPY)
            self.treeview.connect('drag-data-get', self.drag_data_get)
            self.sourceview.connect('drag-data-received',
                self.drag_data_received_data)

            self.sourceview.connect('drag-drop', self.drag_drop)

            self.sourceview.drag_dest_set_target_list(None)
            self.treeview.drag_source_set_target_list(None)
            self.sourceview.drag_dest_add_text_targets()
            self.treeview.drag_source_add_text_targets()

            self.treeview.show_all()
            sc_tree.add(self.treeview)

            self.widget = Gtk.HPaned()
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

    def set_value(self):
        self.field.set_client(self.record, self.get_value())

    def display(self):
        super(SourceView, self).display()
        value = self.field and self.field.get_client(self.record)
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
            if not self.record:
                return
            tree_field = self.record[self.tree_data_field]
            json_data = tree_field.get(self.record)
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
            # MAB: encode function text as bytes instead of str
            selection.set(selection.get_target(), 8, func_text.encode())

    def drag_data_received_data(self, sourceview, context, x, y, selection,
            info, etime):
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
        for tagname in list(ERROR2COLOR.values()):
            tag = tag_table.lookup(tagname)
            self.sourcebuffer.remove_tag(tag, begin, end)
        errors = check_code(self.get_code())
        has_errors = False
        for idx, message in enumerate(errors):
            if (isinstance(message, pyflakes.messages.UndefinedName)
                    and message.message_args[0] in self.known_funcs):
                continue
            error_type = ERROR2COLOR.get(message.__class__, SYNTAX)
            # "9" is the number of lines of the template before the actual
            # code
            has_errors = True
            line_nbr = message.lineno - 9
            self.error_store.append((line_nbr,
                    message.message % message.message_args, error_type))
            line = self.sourcebuffer.props.text.split('\n')[
                line_nbr - 1]
            line_start = self.sourcebuffer.get_iter_at_line_offset(
                line_nbr - 1, 0)
            line_end = self.sourcebuffer.get_iter_at_line_offset(
                line_nbr - 1, len(line))
            self.sourcebuffer.create_source_mark(None, error_type,
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
        self.sourceview.scroll_to_iter(
            textiter, within_margin=0., use_align=True, xalign=0.5, yalign=0.5)
        self.sourcebuffer.place_cursor(textiter)
        GLib.idle_add(self.sourceview.grab_focus)

    def _test_check(self, sourceview, event):
        if Gdk.keyval_name(event.keyval) == 'F7':
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
            for error_type in list(MARKS.keys()):
                sourcebuffer.remove_source_marks(start, end, error_type)
                tag = tag_table.lookup(error_type)
                sourcebuffer.remove_tag(tag, start, end)

    def tree_display_tooltip(self, treeview, x, y, keyboard_mode, tooltip):
        return False
