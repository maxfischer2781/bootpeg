import subprocess
import sys
from bootpeg_examples import math


def test_as_main():
    """Test the example as if run via `python -m`"""
    reply = subprocess.run(
        [sys.executable, "-m", "bootpeg_examples.math"],
        input="1\n2\nexit",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    ).stdout.splitlines()
    assert reply == [f"{math.prompt}{expected}" for expected in ("1", "2", "")]
