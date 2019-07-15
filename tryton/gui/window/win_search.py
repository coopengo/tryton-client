# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import gtk
import gettext

import tryton.common as common
from tryton.common.underline import set_underline
from tryton.config import TRYTON_ICON
from tryton.gui import Main
from tryton.gui.window.nomodal import NoModal
from tryton.gui.window.view_form.screen import Screen
from tryton.gui.window.win_form import WinForm

_ = gettext.gettext


class WinSearch(NoModal):

    def __init__(self, model, callback, sel_multi=True, context=None,
            domain=None, order=None, view_ids=None,
            views_preload=None, new=True, title=''):
        NoModal.__init__(self)
        if view_ids is None:
            view_ids = []
        if views_preload is None:
            views_preload = {}
        self.domain = domain or []
        self.context = context or {}
        self.order = order
        self.view_ids = view_ids
        self.views_preload = views_preload
        self.sel_multi = sel_multi
        self.callback = callback
        self.title = title

        self.win = gtk.Dialog(_('Search'), self.parent,
            gtk.DIALOG_DESTROY_WITH_PARENT)
        Main().add_window(self.win)
        self.win.set_icon(TRYTON_ICON)
        self.win.set_default_response(gtk.RESPONSE_APPLY)
        self.win.connect('response', self.response)

        self.win.set_default_size(*self.default_size())

        self.accel_group = gtk.AccelGroup()
        self.win.add_accel_group(self.accel_group)

        self.but_cancel = self.win.add_button(
            set_underline(_("Cancel")), gtk.RESPONSE_CANCEL)
        self.but_cancel.set_image(common.IconFactory.get_image(
                'tryton-cancel', gtk.ICON_SIZE_BUTTON))
        self.but_cancel.set_always_show_image(True)
        self.but_find = self.win.add_button(
            set_underline(_("Search")), gtk.RESPONSE_APPLY)
        self.but_find.set_image(common.IconFactory.get_image(
                'tryton-search', gtk.ICON_SIZE_BUTTON))
        self.but_find.set_always_show_image(True)
        if new and common.MODELACCESS[model]['create']:
            self.but_new = self.win.add_button(
                set_underline(_("New")), gtk.RESPONSE_ACCEPT)
            self.but_new.set_image(common.IconFactory.get_image(
                    'tryton-create', gtk.ICON_SIZE_BUTTON))
            self.but_new.set_always_show_image(True)
            self.but_new.set_accel_path('<tryton>/Form/New', self.accel_group)

        self.but_ok = self.win.add_button(
            set_underline(_("OK")), gtk.RESPONSE_OK)
        self.but_ok.set_image(common.IconFactory.get_image(
                'tryton-ok', gtk.ICON_SIZE_BUTTON))
        self.but_ok.set_always_show_image(True)
        self.but_ok.add_accelerator('clicked', self.accel_group,
                gtk.keysyms.Return, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        hbox = gtk.HBox()
        hbox.show()
        self.win.vbox.pack_start(hbox, expand=False, fill=True)
        self.win.vbox.pack_start(gtk.HSeparator(), expand=False, fill=True)

        self.screen = Screen(model, domain=domain, mode=['tree'], order=order,
            context=context, view_ids=view_ids, views_preload=views_preload,
            row_activate=self.sig_activate, readonly=True)
        self.view = self.screen.current_view
        # Prevent to set tree_state
        self.screen.tree_states_done.add(id(self.view))
        sel = self.view.treeview.get_selection()
        self.win.set_title(_('Search %s') % self.title)

        if not sel_multi:
            sel.set_mode(gtk.SELECTION_SINGLE)
        else:
            sel.set_mode(gtk.SELECTION_MULTIPLE)
        self.win.vbox.pack_start(self.screen.widget, expand=True, fill=True)
        self.screen.widget.show()

        self.model_name = model

        self.register()

    def sig_activate(self, *args):
        self.view.treeview.emit_stop_by_name('row_activated')
        self.win.response(gtk.RESPONSE_OK)
        return True

    def destroy(self):
        self.screen.destroy()
        self.win.destroy()
        NoModal.destroy(self)

    def show(self):
        self.win.show()

    def hide(self):
        self.win.hide()

    def response(self, win, response_id):
        res = None
        if response_id == gtk.RESPONSE_OK:
            res = [r.id for r in self.screen.selected_records]
        elif response_id == gtk.RESPONSE_APPLY:
            self.screen.search_filter(self.screen.screen_container.get_text())
            return
        elif response_id == gtk.RESPONSE_ACCEPT:
            # Remove first tree view as mode if form only
            view_ids = self.view_ids[1:]
            screen = Screen(self.model_name, domain=self.domain,
                context=self.context, order=self.order, mode=['form'],
                view_ids=view_ids, views_preload=self.views_preload)

            def callback(result):
                if result:
                    record = screen.current_record
                    res = [(record.id, record.value.get('rec_name', ''))]
                    self.callback(res)
                else:
                    self.callback(None)
            self.destroy()
            WinForm(
                screen, callback, new=True, save_current=True,
                title=self.title)
            return
        if res:
            group = self.screen.group
            res = [(id_, group.get(id_).value.get('rec_name', ''))
                for id_ in res]
        self.callback(res)
        self.destroy()
