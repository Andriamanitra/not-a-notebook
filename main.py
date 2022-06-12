import ast
import copy
import contextlib
import io
import sys
from dataclasses import dataclass
import tkinter
from tkinter import BOTH
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class InputCell(tkinter.Frame):
    def __init__(self, parent, depends_on, **kwargs):
        tkinter.Frame.__init__(self, parent, **kwargs)

        self.result = None
        self.depends_on = depends_on

        self.text_input = tkinter.Text(self, height=1)
        self.text_input.pack(fill=BOTH)

        self.result_tabs = nb = ttk.Notebook(self, takefocus=False)

        frame_repr = ttk.Frame(nb)
        self.representation = tkinter.Label(frame_repr, anchor="w")
        self.representation.pack(fill=BOTH)
        nb.add(frame_repr, text="repr")

        frame_stdout = ttk.Frame(nb)
        self.stdout = ScrolledText(frame_stdout, height=2, bg="#DFDFDF")
        self.stdout.pack(fill=BOTH)
        nb.add(frame_stdout, text="stdout")

        frame_stderr = ttk.Frame(nb)
        self.stderr = ScrolledText(frame_stderr, height=2, fg="#FF0000", bg="#DFDFDF")
        self.stderr.pack(fill=BOTH)
        nb.add(frame_stderr, text="stderr")

        # self.text_input.bind("<KeyPress>", self.on_keypress)
        # don't submit on enter if shift or ctrl is pressed
        self.text_input.bind("<Shift-Return>", self.on_shift_return)
        self.text_input.bind("<Control-Return>", self.on_shift_return)
        self.text_input.bind("<Tab>", self.on_tab)
        self.text_input.bind("<Return>", self.submit)

    @property
    def text(self):
        return self.text_input.get(1.0, "end")

    def set_text(self, text):
        self.text_input.delete(1.0, "end")
        self.text_input.insert(1.0, text)

    def cursor_pos(self):
        pos_str = self.text_input.index(tkinter.INSERT)
        row, col = pos_str.split(".")
        return int(row), int(col)

    def on_keypress(self, ev):
        print(ev.keysym, self.cursor_pos())

    def on_tab(self, ev):
        row, col = self.cursor_pos()
        line_before_cursor = self.text_input.get(f"{row}.0", tkinter.INSERT)
        if col == 0 or line_before_cursor.isspace():
            self.text_input.insert(tkinter.INSERT, "    ")
        else:
            ev.widget.tk_focusNext().focus()
        # prevent default
        return "break"

    def on_shift_return(self, ev):
        old_height = self.text_input.cget("height")
        self.text_input.config(height=old_height + 1)

    def submit(self, ev):
        self.set_text(self.text.rstrip())
        row, _col = self.cursor_pos()
        self.text_input.config(height=row)

        if self.depends_on is None:
            result = EvalResult.from_code(self.text, dict())
        else:
            result = EvalResult.from_code(self.text, self.depends_on.result.local_vars)
        self.result = result

        # when executing cell for Nth time some tabs might have
        # been disabled before, so we need to reset
        for i in range(3):
            self.result_tabs.tab(i, state="normal")

        if result.representation is not None:
            self.representation.config(text=result.representation)
            self.result_tabs.select(0)
        else:
            self.result_tabs.tab(0, state="disabled")

        if result.stdout:
            self.stdout.delete(1.0, "end")
            self.stdout.insert(1.0, result.stdout)
            h = min(10, int(self.stdout.index(tkinter.INSERT).split(".")[0]))
            self.stdout.config(height=h)
            self.result_tabs.select(1)
        else:
            self.stdout.config(height=1)
            self.result_tabs.tab(1, state="disabled")

        if result.stderr:
            self.stderr.delete(1.0, "end")
            self.stderr.insert(1.0, result.stderr)
            h = min(10, int(self.stderr.index(tkinter.INSERT).split(".")[0]))
            self.stderr.config(height=h)
            self.result_tabs.select(2)
        else:
            self.stderr.config(height=1)
            self.result_tabs.tab(2, state="disabled")

        if result.representation is not None or result.stdout or result.stderr:
            self.result_tabs.pack(fill=BOTH, expand=True)

        self.event_generate("<<Submit>>")
        # prevent default (which would insert "\n")
        return "break"

    def focus(self):
        self.text_input.focus()


@dataclass
class EvalResult:
    stdout: str
    stderr: str
    representation: str
    local_vars: dict

    @classmethod
    def from_code(cls, code: str, local_vars_before: dict):
        local_vars = dict()
        for name, value in local_vars_before.items():
            try:
                copied = copy.deepcopy(value)
            # some things like modules cannot be deepcopied
            # (hopefully this exception handling doesn't break too many things)
            except TypeError:
                copied = value
            local_vars[name] = copied

        result = None
        my_stdout = io.StringIO()
        my_stderr = io.StringIO()
        with (
                contextlib.redirect_stdout(my_stdout),
                contextlib.redirect_stderr(my_stderr),
        ):
            try:
                body = ast.parse(code).body
                if len(body) == 1 and isinstance(body[0], ast.Expr):
                    result = repr(eval(code, None, local_vars))
                else:
                    exec(code, None, local_vars)
            except Exception as exc:
                print(exc, file=sys.stderr)

        return EvalResult(
            my_stdout.getvalue(),
            my_stderr.getvalue(),
            result,
            local_vars
        )


def main():
    tk = tkinter.Tk()
    tk.title("not a jupyter notebook?")

    def on_submit(ev):
        nonlocal latest_input_cell
        if ev.widget is latest_input_cell:
            make_next_input_cell(latest_input_cell)
        else:
            ev.widget.tk_focusNext().tk_focusNext().focus()

    def make_next_input_cell(prev_cell=None):
        nonlocal tk
        if prev_cell is None or prev_cell.result is None:
            input_widget = InputCell(tk, None)
        else:
            input_widget = InputCell(tk, prev_cell)
        input_widget.bind("<<Submit>>", on_submit)
        input_widget.pack(fill=BOTH)
        input_widget.focus()

        nonlocal latest_input_cell
        latest_input_cell = input_widget

        return input_widget

    latest_input_cell = make_next_input_cell()
    tk.mainloop()


if __name__ == "__main__":
    main()
