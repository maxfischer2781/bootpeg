from bootpeg.pika import boot


def test_bootstrap():
    boot_peg = boot.boot_path.read_text()
    parser = boot.parser
    # ensure each parser handles itself
    for _ in range(2):
        parser = boot.boot(parser, boot_peg)


def test_escalate():
    boot_peg = boot.boot_path.read_text()
    full_peg = boot.full_path.read_text()
    parser = boot.boot(boot.parser, boot_peg)
    for _ in range(2):
        parser = boot.boot(parser, full_peg)
