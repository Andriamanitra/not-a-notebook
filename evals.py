from dataclasses import dataclass
import ast
import io
import contextlib
import sys
import copy


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