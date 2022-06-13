from evals import EvalResult

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "4")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GtkSource
from gi.repository import GObject

language_manager = GtkSource.LanguageManager()
style_scheme_manager = GtkSource.StyleSchemeManager()
print(style_scheme_manager.get_search_path())
# TODO: make this configurable through a menu
print(style_scheme_manager.get_scheme_ids())
COLOR_SCHEME = style_scheme_manager.get_scheme("monokai-extended")


class LineEditor(GtkSource.View):
    def __init__(self):
        super().__init__()
        self.set_monospace(True)
        self.set_show_line_numbers(True)
        self.set_smart_backspace(True)
        self.set_smart_home_end(True)
        self.set_tab_width(4)
        self.set_insert_spaces_instead_of_tabs(True)
        self.set_indent_on_tab(True)
        self.set_auto_indent(True)
        buffer = self.get_buffer()
        buffer.set_language(language_manager.get_language("python3"))
        buffer.set_style_scheme(COLOR_SCHEME)
        buffer.set_highlight_syntax(True)

    @property
    def text(self):
        buffer = self.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)


# TODO: this widget is ugly, figure out a better way to view this stuff
class ReplCellOutputView(Gtk.HBox):
    def __init__(self):
        super().__init__()
        self.repres = Gtk.TextView()
        self.stdout = Gtk.TextView()
        self.stderr = Gtk.TextView()
        self.pack_start(self.repres, expand=True, fill=True, padding=5)
        self.pack_start(self.stdout, expand=True, fill=True, padding=5)
        self.pack_start(self.stderr, expand=True, fill=True, padding=5)
    
    def set_result(self, result: EvalResult):
        if result.representation is not None:
            buf = self.repres.get_buffer()
            buf.set_text(result.representation, len(result.representation))
        if result.stdout is not None:
            buf = self.stdout.get_buffer()
            buf.set_text(result.stdout, len(result.stdout))
        if result.stderr is not None:
            buf = self.stderr.get_buffer()
            buf.set_text(result.stderr, len(result.stderr))


class ReplCell(Gtk.VBox):
    def __init__(self):
        super().__init__()
        self.editor = LineEditor()
        self.output = ReplCellOutputView()
        self.pack_start(self.editor, expand=True, fill=True, padding=5)
        self.pack_start(self.output, expand=False, fill=False, padding=5)
        self.editor.connect("key_press_event", self.key_press_handler)

    def key_press_handler(self, event_source: LineEditor, evk: Gdk.EventKey):
        # eval on shift-enter
        if evk.keyval == Gdk.KEY_Return:
            if evk.state & Gdk.ModifierType.SHIFT_MASK:
                code = event_source.text
                # TODO: use local_vars from previous cell's result instead
                # of an empty dict
                result = EvalResult.from_code(code, dict())
                self.output.set_result(result)
                return True


class ReplWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="not a jupyter notebook")
        self.cell_vbox = Gtk.VBox()
        self.cells = []
        self.add(self.cell_vbox)
        self.connect("destroy", Gtk.main_quit)
        self.connect("key_press_event", self.key_press_handler)

    def add_cell(self):
        cell = ReplCell()
        self.cells.append(cell)
        self.cell_vbox.pack_start(cell, expand=False, fill=False, padding=0)
        self.show_all()
        return cell

    def key_press_handler(self, event_source, evk: Gdk.EventKey):
        # add new cell on ctrl+enter
        if evk.keyval == Gdk.KEY_Return:
            print(evk.state)
            if evk.state & Gdk.ModifierType.CONTROL_MASK:
                cell = self.add_cell()
                cell.editor.grab_focus()
                return True


win = ReplWindow()
win.set_default_size(400, 300)
win.add_cell()
win.show_all()
Gtk.main()
