import importlib_resources

from bootpeg import create_parser, bootpeg_actions
from bootpeg.apegs import boot


def test_bootstrap():
    source = importlib_resources.read_text("bootpeg.grammars", "bpeg.bpeg")
    parser = boot.boot_parser
    # ensure each parser handles itself
    for _ in range(5):
        parser = create_parser(source, parser, bootpeg_actions)
