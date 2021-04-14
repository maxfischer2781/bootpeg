from typing import Optional

import string
import time
import pathlib

from ..utility import ascii_escapes
from .peg import postorder_dfs, ParseFailure, MemoTable, Match
from .front import (
    Literal,
    Sequence,
    Choice,
    Nothing,
    Anything,
    Not,
    And,
    Repeat,
    Reference,
    Parser,
    Debug,
    Capture,
    Rule,
    Action,
    Discard,
    transform,
    chain,
    either,
    Range,
    Delimited,
)


def sum_matches(match: Match) -> int:
    total = 1
    for sub_match in match.sub_matches:
        total += sum_matches(sub_match)
    return total


def range_parse(source: str, parser: Parser):
    """Parse ``source`` showing the matched range"""
    start = time.perf_counter()
    try:
        match, memo = parser.parse(source)
    except ParseFailure as err:
        report_matches(err.memo)
        raise
    until = time.perf_counter()
    print(
        f"Duration: {until - start:4.3f}s",
        f"Matches: {len(memo.matches)} / {len(source)} items",
        f"[{len(memo.matches)/len(source):.1f} m/i]",
        f"Efficiency: {sum_matches(match)} used / {len(memo.matches)} matched",
        f"[{sum_matches(match) / len(memo.matches):.2f} u/m]",
    )
    report_matches(memo)
    return Parser(
        "top",
        **{name: clause for name, clause in transform(match, memo, namespace)[0][0]},
    )


def report_matches(memo: MemoTable):
    """Show matched range(s) by a parsed memo table"""
    longest_matches = {}
    for match in memo.matches.values():
        length, _, position, *_ = match
        if isinstance(match.clause, Repeat) and isinstance(
            match.clause.sub_clauses[0], Anything
        ):
            continue
        if position not in longest_matches or longest_matches[position].length < length:
            longest_matches[position] = match
    report_pos = min(longest_matches)
    print(
        *(" " if i % 10 else i % 1000 // 100 for i in range(len(memo.source))), sep=""
    )
    print(*(" " if i % 10 else i % 100 // 10 for i in range(len(memo.source))), sep="")
    print(*(i % 10 for i in range(len(memo.source))), sep="")
    print(memo.source.translate(ascii_escapes))
    while report_pos < len(memo.source):
        if longest_matches[report_pos].length > 1:
            print(
                " " * report_pos,
                "^",
                "-" * (longest_matches[report_pos].length - 2),
                "^",
                sep="",
            )
            print(" " * report_pos, longest_matches[report_pos].clause)
        report_pos += longest_matches[report_pos].length


def display(parser: Parser):
    """Display a parser in PEG form"""
    try:
        parser._prepare()
    except Exception:
        pass
    else:
        clauses, _, priorities = parser._compiled_parser
        print("Total Rules:", len(list(postorder_dfs(clauses[parser.top]))))
        print(f"{'named rule':<10} <- Prio -", "Clause")
        for name, clause in sorted(clauses.items(), key=lambda n_c: priorities[n_c[1]]):
            print(f"{name:<10} <- {priorities[clause]:4d} -", clause)
            if isinstance(clause, Debug):
                print("Debugs:", clause.sub_clauses[0])


namespace = {
    expression.__name__: expression
    for expression in (
        Literal,
        Sequence,
        chain,
        Choice,
        either,
        Nothing,
        Anything,
        Not,
        And,
        Repeat,
        Reference,
        Capture,
        Rule,
        Action,
        Discard,
        Range,
        Delimited,
    )
}


end_line = Reference("end_line")  # Literal("\n")

#: Minimal parser required to bootstrap the actual parser
min_parser = Parser(
    "top",
    literal=Rule(
        Choice(
            *(
                Sequence(quote, Repeat(Sequence(Not(quote), Anything())), quote)
                for quote in (Literal("'"), Literal('"'))
            )
        ),
        Action("Literal(.*[1:-1])"),
    ),
    spaces=Rule(
        Choice(Repeat(Literal(" ")), Nothing()),
        Action("Discard()"),
    ),
    nothing=Rule(
        Choice(Literal("''"), Literal('""')),
        Action("Nothing()"),
    ),
    anything=Rule(
        Literal("."),
        Action("Anything()"),
    ),
    end_line=Rule(
        Literal("\n"),
        Action("Discard()"),
    ),
    identifier=Rule(
        Repeat(Choice(*(Literal(ch) for ch in string.ascii_letters + "_"))),
        Action(".*"),
    ),
    choice=Rule(
        Sequence(
            Capture("try", Reference("expr")),
            Reference("spaces"),
            Literal("|"),
            Reference("spaces"),
            Capture("else", Reference("expr")),
        ),
        Action("either(.try, .else)"),
    ),
    group=Rule(
        Sequence(
            Literal("("),
            Reference("spaces"),
            Capture("expr", Reference("expr")),
            Reference("spaces"),
            Literal(")"),
        ),
        Action(".expr"),
    ),
    sequence=Rule(
        Sequence(
            Capture("head", Reference("expr")),
            Reference("spaces"),
            Capture("tail", Reference("expr")),
        ),
        Action("chain(.head, .tail)"),
    ),
    repeat=Rule(
        Sequence(Capture("expr", Reference("expr")), Reference("spaces"), Literal("+")),
        Action("Repeat(.expr)"),
    ),
    reference=Rule(
        Capture("name", Reference("identifier")),
        Action("Reference(.name)"),
    ),
    capture=Rule(
        Sequence(
            Capture("name", Reference("identifier")),
            Reference("spaces"),
            Literal("="),
            Reference("spaces"),
            Capture("expr", Choice(Reference("reference"), Reference("group"))),
        ),
        Action("Capture(.name, .expr)"),
    ),
    reject=Rule(
        Sequence(Literal("!"), Reference("spaces"), Capture("expr", Reference("expr"))),
        Action("Not(.expr)"),
    ),
    expr=Rule(
        Capture(
            "expr",
            Choice(
                Reference("choice"),
                Reference("sequence"),
                Reference("repeat"),
                Reference("capture"),
                Reference("reference"),
                Reference("group"),
                Reference("literal"),
                Reference("reject"),
                Reference("anything"),
                Reference("nothing"),
            ),
        ),
        Action(".expr"),
    ),
    action=Rule(
        Sequence(
            Literal("{"),
            Capture("body", Repeat(Sequence(Not(Literal("}")), Anything()))),
            Literal("}"),
        ),
        Action("Action(.body)"),
    ),
    rule=Rule(
        Sequence(
            Literal("|"),
            Reference("spaces"),
            Capture("expr", Reference("expr")),
            Reference("spaces"),
            Capture("action", Reference("action")),
        ),
        Action("Rule(.expr, .action)"),
    ),
    rules=Choice(
        Rule(
            Sequence(
                Literal(" "),
                Reference("spaces"),
                Capture("try", Reference("rule")),
                Reference("spaces"),
                end_line,
                Capture("else", Reference("rules")),
            ),
            Action("either(.try, .else)"),
        ),
        Rule(
            Sequence(
                Literal(" "),
                Reference("spaces"),
                Capture("rule", Reference("rule")),
                Reference("spaces"),
                end_line,
            ),
            Action(".rule"),
        ),
    ),
    define=Rule(
        Sequence(
            Capture("name", Reference("identifier")),
            Literal(":"),
            Reference("spaces"),
            end_line,
            Capture("rules", Reference("rules")),
        ),
        Action("(.name, .rules)"),
    ),
    comment=Rule(
        Sequence(Literal("#"), Repeat(Sequence(Not(end_line), Anything())), end_line),
        Action("Discard()"),
    ),
    blank=Rule(
        Sequence(Reference("spaces"), end_line),
        Action("Discard()"),
    ),
    top=Rule(
        Repeat(Choice(Reference("define"), Reference("comment"), Reference("blank"))),
        Action(".*"),
    ),
)
boot_path = pathlib.Path(__file__).parent / "boot.bpeg"
full_path = pathlib.Path(__file__).parent.parent / "grammars" / "bpeg.bpeg"


def boot(base_parser: Parser, source: str) -> Parser:
    head, memo = base_parser.parse(source)
    assert head.length == len(source)
    results, _ = transform(head, memo, namespace)
    return Parser(
        "top",
        **{name: clause for name, clause in results[0]},
    )


_parser_cache: Optional[Parser] = None


def bootpeg() -> Parser:
    """Provide the basic bootpeg Pika parser"""
    global _parser_cache
    if _parser_cache is None:
        _parser_cache = boot(min_parser, boot_path.read_text())
    return _parser_cache


if __name__ == "__main__":
    parser = bootpeg()
    for iteration in range(2):
        with open(boot_path) as boot_peg:
            print("Generation:", iteration)
            display(parser)
            parser = range_parse(
                boot_peg.read(),
                parser,
            )
    for iteration in range(2, 4):
        with open(full_path) as base_peg:
            print("Generation:", iteration)
            display(min_parser)
            parser = range_parse(
                base_peg.read(),
                parser,
            )
    display(parser)
