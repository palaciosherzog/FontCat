
from fontwindow import FontWindow

import sys
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class FontCat(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.github.palaciosherzog.fontcat", *kwargs)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        css = b"""
        .small-button {
        min-height: 0px;
        min-width: 0px;
        padding: 0px 5px;
        margin: 0px;
        border-radius: 20px;
        background: none;
        border: none;
        }
        .tag-label {
            background-color: @selected_bg_color;
            color: @selected_fg_color;
            border-radius: 20px;
            padding: 0px;
        }
        """

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        if not self.window:
            self.window = FontWindow(application=self, title="Font Cat")

        self.window.present()


if __name__ == "__main__":
    FontCat().run(sys.argv)
