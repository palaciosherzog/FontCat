import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Pango, PangoCairo


class FontPrint:
    def __init__(self, parent_window, font_model=None, last_query=None,
                 margin_btwn=10, arial_size=10):
        self.operation = Gtk.PrintOperation()
        self.parent_window = parent_window
        self.font_model = font_model
        self.font_list = font_model.get_filtered_fonts(last_query)
        self.columns = self.font_model.columns
        self.arial_size = arial_size
        self.margin_btwn = margin_btwn

        self.operation.connect('begin-print', self.begin_print, None)
        self.operation.connect('draw-page', self.draw_page, None)

    def begin_print(self, operation, context, print_data):
        operation.set_unit(Gtk.Unit.MM)
        def ciel_div(x, y): return x//y if x % y == 0 else x//y+1
        height = context.get_height()
        self.rows_per_page = int((height + self.margin_btwn) /
                                 (self.font_model.view_size + self.arial_size + 3 + self.margin_btwn))
        needed_rows = ciel_div(len(self.font_list), self.columns)
        num_pages = max(1, ciel_div(needed_rows, self.rows_per_page))
        operation.set_n_pages(num_pages)

    def draw_page(self, operation, context, page_num, print_data):
        width = context.get_width()
        cr = context.get_cairo_context()
        box_width = (width - ((self.columns-1) *
                     self.margin_btwn)) / self.columns

        fonts_per_page = self.columns*self.rows_per_page
        start = page_num*fonts_per_page
        fonts = self.font_list[start:start+fonts_per_page]
        for i, font in enumerate(fonts):
            cr.set_source_rgb(0, 0, 0)
            x = (i % self.columns) * (box_width + self.margin_btwn)
            y = (i // self.columns) * (self.font_model.view_size +
                                       self.arial_size + 3 + self.margin_btwn)
            name_layout = PangoCairo.create_layout(cr)
            name_layout.set_markup(
                f"<span font=\"sans serif {self.arial_size}px\">{font}</span>")
            name_layout.set_ellipsize(Pango.EllipsizeMode.END)
            name_layout.set_width(box_width * Pango.SCALE)
            cr.move_to(x, y)
            PangoCairo.show_layout(cr, name_layout)
            y += self.arial_size + 3
            new_layout = PangoCairo.create_layout(cr)
            disp_text = font if self.font_model.view_text == "{font_name}" else self.font_model.view_text
            new_layout.set_markup(
                f"<span font=\"{font} {self.font_model.view_size}px\">{disp_text}</span>")
            new_layout.set_ellipsize(Pango.EllipsizeMode.END)
            new_layout.set_width(box_width * Pango.SCALE)
            new_layout.set_height(self.font_model.view_size * Pango.SCALE)
            w, h = new_layout.get_pixel_size()
            #cr.rectangle(x, y, box_width, self.font_model.view_size)
            #cr.set_source_rgb(0, (fonts_per_page-i)/fonts_per_page, (fonts_per_page-i)/fonts_per_page)
            # cr.fill()
            y -= (h - self.font_model.view_size)/2  # fixes vertical alignment
            # NOTE: may make text overlap on the top, but otherwise it does on the bottom, so...
            #cr.rectangle(x, y, w, h)
            #cr.set_source_rgba(i/fonts_per_page, i/fonts_per_page, 0, 0.5)
            # cr.fill()
            cr.set_source_rgb(0, 0, 0)
            cr.move_to(x, y)
            PangoCairo.show_layout(cr, new_layout)

    def run(self):
        self.operation.set_embed_page_setup(True)
        result = self.operation.run(Gtk.PrintOperationAction.PRINT_DIALOG,
                                    self.parent_window)

        if result == Gtk.PrintOperationResult.ERROR:
            message = self.operation.get_error()
            dialog = Gtk.MessageDialog(self.parent_window, 0,
                                       Gtk.MessageType.ERROR,
                                       Gtk.ButtonsType.CLOSE,
                                       message)
            dialog.run()
            dialog.destroy()
