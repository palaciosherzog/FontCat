import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class EntryDialog(Gtk.Dialog):
    def __init__(self, parent, title, prompt='', default='', reset=None, valid_func=None):
        super().__init__(title=title, transient_for=parent, flags=0)
        self.reset_val = reset
        self.valid_func = valid_func
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.set_default_size(150, 100)

        user_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.user_entry = Gtk.Entry()
        self.user_entry.connect('changed', self.set_sensitivity)
        self.user_entry.set_text(default)
        user_box.pack_start(self.user_entry, True, True, 6)
        if reset is not None:
            reset_btn = Gtk.Button(label="\u21BB")
            reset_btn.connect('clicked', self.reset)
            user_box.pack_start(reset_btn, False, False, 6)
        label = Gtk.Label(label=prompt)
        label.set_line_wrap(True)

        box = self.get_content_area()
        box.add(label)
        box.add(user_box)
        self.show_all()

    def reset(self, button):
        self.user_entry.set_text(self.reset_val)

    def set_sensitivity(self, entry):
        if self.valid_func is not None:
            self.set_response_sensitive(
                Gtk.ResponseType.OK, self.valid_func(entry.get_text()))

    def run(self):
        return super().run(), self.user_entry.get_text()