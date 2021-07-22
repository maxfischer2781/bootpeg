import importlib_resources
import pickle

import pytest

from bootpeg import create_parser, actions
from bootpeg.apegs import boot


def test_bootstrap():
    source = importlib_resources.read_text("bootpeg.grammars", "bpeg.bpeg")
    parser = boot.boot_parser
    # ensure each parser handles itself
    for _ in range(5):
        parser = create_parser(source, parser, actions)


@pytest.mark.parametrize("protocol", list(range(2, pickle.HIGHEST_PROTOCOL + 1)))
def test_pickle(protocol):
    """Ensure that parsers can be pickled"""
    source = importlib_resources.read_text("bootpeg.grammars", "bpeg.bpeg")
    parser = boot.boot_parser
    for _ in range(2):
        parser = pickle.loads(pickle.dumps(parser, protocol=protocol))
        parser = create_parser(source, parser, actions)
