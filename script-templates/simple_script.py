#!/usr/bin/env python3
"""
SCRIPT_DESCRIPTION

Usage: {script} [options] [PATH]

Arguments:
    PATH - Path to the directory, where script should run.
           If not specified, use current directory.

Options:
    -h, --help
        Show this screen and exit.
"""

import sys
from contextlib import suppress
from pathlib import Path


def main(script_name: str, *script_args: str):
    doc = __doc__.format(script=Path(script_name).name)
    args = __import__("docopt").docopt(doc, script_args)
    path = Path(args["PATH"] or ".")


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        main(sys.argv[0], *sys.argv[1:])
