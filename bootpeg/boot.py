import sys
import re
from functools import partial

from .peg import Regex, Grammar, Action, ForwardReference, Parser, Rule, Inspect, Match


sys.setrecursionlimit(sys.getrecursionlimit()*2)


# Minimal parser required to bootstrap an entire EBNF PEG parser
# manually maintained, should be in sync with boot.peg
class Define:
    def __init__(self, name: str, rule: Rule):
        self.name = name
        self.rule = rule

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name}, ...)"


namespace = {
    **{
        expression.__name__: expression for expression in
        (Define, Regex, Grammar, Action, ForwardReference, Parser, Rule, Inspect, Match)
    },
    're': re,
}
namespace['ParseAction'] = ParseAction = partial(Action, namespace=namespace)


spaces = Regex(r"\ *")
end_line = Regex("\n")
identifier = Regex(r"[a-zA-Z_]+")
expr = ForwardReference("expr")
boot = Parser(
    Grammar(
        literal=Rule(
            Regex(r'"[^"]+"') | Regex(r"'[^']+'"),
            ParseAction("Regex(re.escape(.*))"),
        ),
        choice=Rule(
            expr.label("first") + spaces + Regex(r"\|") + spaces + ~expr.label("else"),
            ParseAction(".first | .else"),
        ),
        group=Rule(
            Regex(r"\(") + spaces + ~expr.label("sub") + spaces + ~Regex(r"\)"),
            ParseAction(".sub"),
        ),
        chain=Rule(
            expr + spaces + expr,
            ParseAction(".0 + .2"),
        ),
        repeat=Rule(
            expr + spaces + Regex(r"\+"),
            ParseAction(".0[0:]"),
        ),
        capture=Rule(
            identifier.label("label") + spaces + Regex("=") + spaces + ~expr.label("expr"),
            ParseAction("(.expr).label(.label)"),
        ),
        reference=Rule(
            identifier,
            ParseAction("ForwardReference(.0)"),
        ),
        expr=Rule(
            ForwardReference("choice") | ForwardReference("chain") | ForwardReference("repeat") | ForwardReference("group") | ForwardReference("capture") | ForwardReference("reference") | ForwardReference("literal"),
            ParseAction(".0"),
        ),
        rule=Rule(
            Regex(r"\|") + spaces + ~expr.label("body") + spaces + ~ForwardReference("action").label("action"),
            ParseAction("Rule(.body, .action)"),
        ),
        action=Rule(
            Regex("{") + Regex(r"[^}]*").label("body") + spaces + Regex("}"),
            ParseAction("ParseAction(.body)")
        ),
        comment=Rule(
            Regex("#.*?\n"),
            ParseAction(""),
        ),
        empty=Rule(
            (spaces + end_line),
            ParseAction(""),
        ),
        define=Rule(
            identifier.label("name") + Regex(":") + spaces + end_line + ForwardReference("rules").label("rules"),
            ParseAction("Define(.name, .rules)"),
        ),
        rules=Rule(
            Regex(r"\ ") + spaces + (
                Rule(
                    ForwardReference("rule").label("first") + spaces + end_line + ForwardReference("rules").label("else"),
                    ParseAction(".first | .else"),
                )
                | Rule(
                    ForwardReference("rule") + spaces + end_line,
                    ParseAction(".0"),
                )
            ).label("rules"),
            ParseAction(".rules"),
        ),
        top=Rule(
            (ForwardReference("comment") | ForwardReference("define") | ForwardReference("empty"))[1:],
            ParseAction(".*"),
        )
    ),
    top="top",
)


if __name__ == "__main__":
    from pathlib import Path
    print(boot.parse((Path(__file__).parent / "boot.peg").read_text()))
