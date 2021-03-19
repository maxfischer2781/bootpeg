from bootpeg.pika import boot


def test_bootstrap():
    with open(boot.boot_path) as boot_peg_stream:
        boot_peg = boot_peg_stream.read()
    parser = boot.parser
    for _ in range(2):
        parser = boot.boot(parser, boot_peg)
