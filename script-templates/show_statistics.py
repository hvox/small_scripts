#!/usr/bin/env python3
"""
SCRIPT_DESCRIPTION

Usage: {script} [options]

Options:
    -h, --help
        Show this screen and exit.
"""

import sys
from contextlib import suppress
from pathlib import Path


def main(script_name: str, *script_args: str):
    doc = __doc__.format(script=Path(script_name).name)
    if script_args:
        print(doc.lstrip())
        exit(len(script_args) != 1 or script_args[0] not in ["-h", "--help"])
    pass


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        main(sys.argv[0], *sys.argv[1:])
