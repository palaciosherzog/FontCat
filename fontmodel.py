import json


class FontCatModel:

    def __init__(self, font_list, filename):
        '''
        font_list : list of font names, gotten from pango context
        filename : filename where tags of the fonts are stored
        '''
        self.font_list = font_list
        self.filename = filename

        self.show_tags = True
        self.columns = -1
        self.view_size = 16
        self.view_text = "{font_name}"

        self.font_tags = {}
        self.all_tags = {}
        for font in self.font_list:
            self.font_tags[font] = []

        if filename is not None:
            self.load_file()

    def load_file(self):
        '''Attempts to open file from filename specified in constructor.
        Tries to get json, and creates lists from json.'''
        with open(self.filename) as tags_file:
            tags_list = json.load(tags_file)
            for k, vals in tags_list.items():
                self.all_tags[k] = len(vals)
                for v in vals:
                    if v in self.font_tags:
                        self.font_tags[v].append(k)

    def save_file(self):
        '''Attempts to write file in proper format to filename specified in constructor.'''
        tags_list = {}
        for key in self.all_tags.keys():
            tags_list[key] = []
        for k, vals in self.font_tags.items():
            for v in vals:
                tags_list[v] += [k]
        with open(self.filename, 'w') as tags_file:
            json.dump(tags_list, tags_file)

    def get_all_fonts(self):
        '''Returns list of all fonts given in constructor.'''
        return self.font_list

    def get_filtered_fonts(self, query):
        '''Returns list of all fonts that satisfy query.'''
        return list(filter(lambda fn: FontCatModel.filter_func(
            self.get_font_name_w_tags(fn), query, False), self.font_list))

    def get_all_tags(self):
        '''Returns list of all current tags.'''
        return self.all_tags.keys()

    def remove_tag_from_all(self, tag):
        '''Removes tag from list of current tags and from all fonts.'''
        del self.all_tags[tag]
        for v in self.font_tags.values():
            if tag in v:
                v.remove(tag)

    def get_font_name_w_tags(self, font_name):
        '''Returns string of font name and tags, used for filtering.'''
        return f'{font_name} : {"{" + "},{".join(self.get_font_tags(font_name)) + "}"}'

    def get_font_tags(self, font_name):
        '''Returns list of tags that a font has'''
        return self.font_tags[font_name]

    def add_tag(self, font_name, text):
        '''Attempts to add tag to list of tags for font_name.
        Returns if parent window tag flowbox needs to be reloaded.'''
        if text not in self.font_tags[font_name]:
            self.font_tags[font_name].append(text)
            if text in self.all_tags:
                self.all_tags[text] += 1
            else:
                self.all_tags[text] = 1
                return True
        return False

    def rmv_tag(self, font_name, tag):
        '''Attemps to remove tag from list of tags of font_name.
        Returns if parent window tag flowbox needs to be reloaded.'''
        if tag in self.font_tags[font_name]:
            self.font_tags[font_name].remove(tag)
            self.all_tags[tag] -= 1
            if self.all_tags[tag] == 0:
                del self.all_tags[tag]
                return True
        return False

    # TODO: should this be in this class?
    def filter_func(item, search_text, fb_filter=True):
        '''Function that parses filter.'''
        if fb_filter:
            item = item.get_name()

        if search_text == '{{All Fonts}}':
            return True
        try:
            stack = []
            op_dict = {
                "!": lambda x, y: not y,
                "|": lambda x, y: x or y,
                "&": lambda x, y: x and y,
            }

            def eval_stack():
                right = stack.pop()
                op = stack.pop()
                if op == '(':
                    stack.append(right)
                    return False
                left = None if op == '!' else stack.pop()
                stack.append(op_dict[op](left, right))
                return True
            i, start = 0, -1
            while i < len(search_text):
                if search_text[i] == '}':
                    stack.append(search_text[start:i+1] in item)
                    start = -1
                elif start == -1:
                    if search_text[i] == '{':
                        start = i
                    elif search_text[i] == ')':
                        cont_eval = True
                        while cont_eval:
                            cont_eval = eval_stack()
                    elif search_text[i] == '(':
                        stack.append('(')
                    elif search_text[i] == '!' or search_text[i:i+3].lower() == 'not':
                        stack.append('!')
                    elif search_text[i] == '|' or search_text[i:i+2].lower() == 'or':
                        stack.append('|')
                    elif search_text[i] == '&' or search_text[i:i+3].lower() == 'and':
                        stack.append('&')
                i += 1
            while len(stack) > 1:
                eval_stack()
            return stack[0]
        except:
            return False
