import pytest

from bootpeg.pika import boot


def test_bootstrap():
    boot_peg = boot.boot_path.read_text()
    parser = boot.min_parser
    # ensure each parser handles itself
    for _ in range(2):
        parser = boot.boot(parser, boot_peg)


def test_escalate():
    full_peg = boot.full_path.read_text()
    parser = boot.bootpeg()
    for _ in range(2):
        parser = boot.boot(parser, full_peg)


def test_features():
    full_peg = boot.full_path.read_text()
    parser = boot.boot(boot.bootpeg(), full_peg)
    opt_repeat = boot.boot(parser, 'rule:\n    | [ " "+ ]\n')
    non_repeat = boot.boot(parser, 'rule:\n    | " "*\n')
    assert opt_repeat.clauses == non_repeat.clauses
    with pytest.raises(TypeError):
        boot.boot(parser, 'rule:\n    | [ " "+ ] { .missing }\n')
    with pytest.raises(TypeError):
        boot.boot(parser, 'rule:\n    | extra=([ " "+ ]) { () }\n')
