from typing import Optional
from pathlib import Path

from ..pika.peg import (
    Parser,
)
from ..api import Actions, PikaActions, parse as generic_parse
from . import bpeg

_parser_cache: Optional[Parser] = None
grammar_path = Path(__file__).parent / "peg.bpeg"


def _get_parser() -> Parser:
    global _parser_cache
    if _parser_cache is None:
        parser = bpeg.parse(grammar_path.read_text())
        _parser_cache = parser
    return _parser_cache


def parse(source, actions: Actions = PikaActions):
    return generic_parse(source, _get_parser(), actions)
