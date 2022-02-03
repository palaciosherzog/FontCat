from fontmodel import FontCatModel
from fontprint import FontPrint
from customdialog import EntryDialog

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, Pango


class TagFlowbox(Gtk.FlowBox):

    def __init__(self, tag_list=None, add_func=None, rmv_func=None, filter_func=None):
        super().__init__()
        self.tag_list = tag_list
        self.add_func = add_func
        self.rmv_func = rmv_func
        self.filter_func = filter_func

        self.set_max_children_per_line(10)
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        if self.filter_func is not None:
            self._add_tag_box(label=('All Fonts', self.filter_func))
        for tag in self.tag_list:
            self._add_tag_box(label=(tag, self.filter_func),
                              button=('-', self.rmv_func))
        if add_func is not None:
            self._add_tag_box(label=('+', self.add_func))

    def _add_tag_box(self, label, button=None):
        tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        if label[1] is not None:
            tag_label = Gtk.Button(label=label[0])
            tag_label.get_style_context().add_class('small-button')
            tag_label.connect("clicked", label[1], label[0])
        else:
            tag_label = Gtk.Label(label=label[0])
        tag_box.pack_start(tag_label, True, True, 3)
        if button is not None:
            tag_btn = Gtk.Button(label=button[0])
            tag_btn.get_style_context().add_class('small-button')
            tag_btn.connect("clicked", button[1], label[0])
            tag_box.pack_end(tag_btn, False, False, 0)
        tag_box.get_style_context().add_class('tag-label')
        self.add(tag_box)


class FontBox(Gtk.FlowBoxChild):

    def __init__(self, parent_window, font_name, font_model):
        super().__init__()
        self.parent_window = parent_window
        self.font_name = font_name
        self.font_model = font_model
        self.tag_list = font_model.get_font_tags(font_name)
        self.reload_name()
        self.add_font_box()

    def reload_name(self):
        self.set_name(self.font_model.get_font_name_w_tags(self.font_name))

    def add_font_box(self):
        '''Creates and adds box with frame with font name and font name in font'''
        new_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        new_frame = Gtk.Frame(label=self.font_name)
        new_label = Gtk.Label(label=self.font_name)
        new_label.set_xalign(0)
        disp_text = self.font_name if self.font_model.view_text == "{font_name}" else self.font_model.view_text
        new_label.set_markup(
            f"<span font=\"{self.font_name} {self.font_model.view_size}\">{disp_text}</span>")
        new_label.set_ellipsize(Pango.EllipsizeMode.END)
        new_frame.add(new_label)
        new_frame.set_size_request(120, 60)
        new_box.pack_start(new_frame, False, False, 0)
        new_box.pack_start(TagFlowbox(tag_list=self.tag_list,
                                      add_func=self.add_tag,
                                      rmv_func=self.rmv_tag),
                           False, False, 0)
        self.add(new_box)

    def reload_tag_flowbox(self):
        '''Replaces the old tag flowbox with a newly created tag flowbox,'''
        box = self.get_children()[0]
        tag_flowbox = box.get_children()[1]
        box.remove(tag_flowbox)
        new_tag_flowbox = TagFlowbox(
            tag_list=self.tag_list, add_func=self.add_tag, rmv_func=self.rmv_tag)
        box.pack_start(new_tag_flowbox, False, False, 0)
        new_tag_flowbox.show_all()

    def add_tag(self, button, tag):
        '''Creates and shows dialog window for input of tag. 
        Gets input and reloads tag flowbox.'''
        dialogWindow = EntryDialog(
            parent=self.parent_window, title="Add tag",
            prompt="Enter text for tag\nDo not include '{' or '}'",
            valid_func=lambda x: '{' not in x and '}' not in x)
        response, text = dialogWindow.run()
        dialogWindow.destroy()

        if (response == Gtk.ResponseType.OK) and (text != ''):
            if self.font_model.add_tag(self.font_name, text):
                self.parent_window.reload_tag_flowbox()
            self.reload_tag_flowbox()
            self.reload_name()

    def rmv_tag(self, button, tag):
        '''Removes tag. Reloads parent window flowbox if needed'''
        if self.font_model.rmv_tag(self.font_name, tag):
            self.parent_window.reload_tag_flowbox()
        self.reload_tag_flowbox()
        self.reload_name()


class FontWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, filename="tags.json", **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(800, 400)

        self.font_model = FontCatModel(self.list_system_fonts(), filename)

        self._create_window()
        self._create_actions()
        self.show_all()

    def _create_window(self):
        '''Creates the headerbar with custom menu, along with all widgets, and adds them to the window.'''
        # create custom header bar with custom menu ui
        header_bar = Gtk.HeaderBar(show_close_button=True, title="Font Cat")
        menu = Gtk.Builder.new_from_file("menu.ui").get_object("main_menu")
        menu_icon = Gtk.Image.new_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.MENU)
        menu_button = Gtk.MenuButton(direction=Gtk.ArrowType.DOWN,
                                     use_popover=False,
                                     menu_model=menu)
        menu_button.add(menu_icon)
        header_bar.add(menu_button)
        header_bar.show_all()
        self.set_titlebar(header_bar)

        # add widgets in the window
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # add search box
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.connect('search_changed', self.search_flowbox_filter)
        self.search_entry.set_text('{All Fonts}')
        vbox.pack_start(self.search_entry, False, False, 6)

        # add main flowbox with unique list of tags
        vbox.pack_start(TagFlowbox(tag_list=self.font_model.get_all_tags(),
                                   rmv_func=self.remove_tag,
                                   filter_func=self.flowbox_filter),
                        False, False, 0)

        # create scrolling window of all fonts with tags
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.get_flowbox_of_fonts())
        vbox.pack_start(scrolled, True, True, 0)

        self.add(vbox)

    def _create_actions(self):
        '''Creates the menu actions and connects them.'''
        actions = [
            ('save', self.save_file),
            ('print', self.export_pdf),
            ('hide_tags', self.toggle_tags),
            ('set_columns', self.set_columns),
            ('set_size', self.set_size),
            ('set_text', self.set_text),
        ]
        for action_name, callback in actions:
            action = Gio.SimpleAction.new(action_name, None)
            action.connect("activate", callback)
            self.add_action(action)

    def save_file(self, action, param):
        '''Calls for the font_model to overwrite the tags file.'''
        self.font_model.save_file()

    def export_pdf(self, action, param):
        '''Calls for print operation to be run with current settings.'''
        # TODO: should there be a dialog to customize all of the customizable settings?
        dialogWindow = EntryDialog(
            parent=self, title="Set Columns",
            prompt="Enter number of columns to print with (1-12)",
            default=str(
                self.font_model.columns) if self.font_model.columns != -1 else "3",
            reset="3",
            valid_func=lambda x: x.isdigit() and int(x) > 0 and int(x) <= 12)
        response, text = dialogWindow.run()
        dialogWindow.destroy()
        if response == Gtk.ResponseType.OK:
            self.font_model.columns = int(text)
            FontPrint(parent_window=self, font_model=self.font_model,
                      last_query=self.search_entry.get_text()).run()

    def toggle_tags(self, action, param):
        '''Makes the tags disappear, for less busy comparison of fonts.'''
        self.font_model.show_tags = not self.font_model.show_tags
        def toggle(x): return x.show(
        ) if self.font_model.show_tags else x.hide()
        font_flowbox = self.get_children()[0].get_children()[
            2].get_children()[0].get_children()[0]
        for fb_child in font_flowbox.get_children():
            toggle(fb_child.get_children()[0].get_children()[1])
        toggle(self.get_children()[0].get_children()[1])

    def set_columns(self, action, param):
        dialogWindow = EntryDialog(
            parent=self, title="Set Columns",
            prompt="Enter number of columns to display (1-12)",
            default=str(
                self.font_model.columns) if self.font_model.columns != -1 else "dynamic",
            reset="dynamic",
            valid_func=lambda x: x == "dynamic" or (x.isdigit() and int(x) > 0 and int(x) <= 12))
        response, text = dialogWindow.run()
        dialogWindow.destroy()
        if response == Gtk.ResponseType.OK:
            if text == 'dynamic':
                self.font_model.columns = -1
                self.reload_font_flowbox()
            else:
                self.font_model.columns = int(text)
                self.reload_font_flowbox()

    def set_size(self, action, param):
        dialogWindow = EntryDialog(
            parent=self, title="Set Display Text Size",
            prompt="Enter size of text for preview in px (4-128)",
            default=str(self.font_model.view_size), reset='16',
            valid_func=lambda x: x.isdigit() and int(x) >= 4 and int(x) <= 128)
        response, text = dialogWindow.run()
        dialogWindow.destroy()
        if response == Gtk.ResponseType.OK:
            self.font_model.view_size = int(text)
            self.reload_font_flowbox()

    def set_text(self, action, param):
        dialogWindow = EntryDialog(
            parent=self, title="Set Display Text",
            prompt="Enter the text to display", default=str(self.font_model.view_text),
            reset="{font_name}")
        response, text = dialogWindow.run()
        dialogWindow.destroy()
        if response == Gtk.ResponseType.OK:
            self.font_model.view_text = text
            self.reload_font_flowbox()

    def list_system_fonts(self):
        ''' Yield system fonts families using Pango. '''
        context = self.create_pango_context()
        return [fam.get_name() for fam in context.list_families()]

    def get_flowbox_of_fonts(self):
        '''Create flowbox with all of the fonts in their respective boxes.'''
        # make flowbox and set all settings
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        if self.font_model.columns == -1:
            self.flowbox.set_min_children_per_line(1)
            self.flowbox.set_max_children_per_line(12)
        else:
            self.flowbox.set_min_children_per_line(self.font_model.columns)
            self.flowbox.set_max_children_per_line(self.font_model.columns)
        self.flowbox.set_homogeneous(True)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)

        # get each font in its appropriate box
        for fn in self.font_model.get_all_fonts():
            self.flowbox.add(FontBox(parent_window=self,
                             font_name=fn, font_model=self.font_model))
        return self.flowbox

    def reload_tag_flowbox(self):
        '''Replaces the old tag flowbox with a newly created tag flowbox,'''
        box = self.get_children()[0]
        tag_flowbox = box.get_children()[1]
        box.remove(tag_flowbox)
        new_tag_flowbox = TagFlowbox(tag_list=self.font_model.get_all_tags(),
                                     rmv_func=self.remove_tag,
                                     filter_func=self.flowbox_filter)
        box.pack_start(new_tag_flowbox, False, False, 0)
        box.reorder_child(new_tag_flowbox, 1)
        new_tag_flowbox.show_all()

    def reload_font_flowbox(self):
        '''Replaces the old font flowbox with a newly created font flowbox.'''
        box = self.get_children()[0].get_children()[2]
        font_flowbox = box.get_children()[0]
        box.remove(font_flowbox)
        new_font_flowbox = self.get_flowbox_of_fonts()
        box.add(new_font_flowbox)
        new_font_flowbox.show_all()
        self.flowbox_filter(None, self.search_entry.get_text())

    def remove_tag(self, button, tag):
        '''Confirms that user wants to remove tag from all entries.
        If confirmed, removes in model, and reloads font & tag flowbox.'''
        if button is not None:
            msg = 'This will remove this tag from all entries.\nAre you sure you want to continue?'
            d = Gtk.MessageDialog(transient_for=self,
                                  modal=True,
                                  message_type=Gtk.MessageType.WARNING,
                                  buttons=Gtk.ButtonsType.OK_CANCEL,
                                  text=msg)
            response = d.run()
            d.destroy()

            if response == Gtk.ResponseType.OK:
                self.font_model.remove_tag_from_all(tag)
                self.reload_font_flowbox()
                self.reload_tag_flowbox()

    def search_flowbox_filter(self, search_entry):
        '''When search entry text is changed, filter flowbox with text.'''
        self.flowbox_filter(None, search_entry.get_text())

    def flowbox_filter(self, button, filter_text):
        '''Fixes format when button clicked and filters flowbox with search text.'''
        if button is not None or filter_text == '{All Fonts}':
            filter_text = "{" + filter_text + '}'
            self.search_entry.set_text(filter_text)
        self.flowbox.set_filter_func(FontCatModel.filter_func, filter_text)
