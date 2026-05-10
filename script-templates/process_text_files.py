#!/usr/bin/env python3
"""
SCRIPT_DESCRIPTION

Usage: {script} [options] [PATH]

Arguments:
    PATH - Path to the file or directory with files.
           If not specified, use current directory.

Options:
    -h, --help
        Show this screen and exit.

    --verbose
        Raise verbosity level.

    -z, --zero-terminated
        Outputted items are terminated by NUL rather than EOL.
"""

import sys
from contextlib import suppress
from pathlib import Path


def process(text: str):
    lines = text.splitlines()
    for line in lines:
        emit(line)


def main(script_name: str, *script_args: str):
    doc = __doc__.format(script=Path(script_name).name)
    args = __import__("docopt").docopt(doc, script_args)
    setattr(debug, "enabled", args["--verbose"])
    setattr(emit, "eol", "\x00" if args["--zero-terminated"] else "\n")
    debug(f"Running with arguments {dict(args)!r}")
    paths = [Path(args["PATH"] or ".")]
    for path in paths:
        if path.is_dir():
            paths.extend(path.iterdir())
        elif path.is_file():
            debug(f"Processing {path}")
            try:
                process(path.read_text(encoding="utf-8", errors="strict"))
            except UnicodeDecodeError:
                debug(f"  Failure: {path} is binary file")


def emit(*objects: object, sep: str = " "):
    print(sep.join(map(str, objects)), end=getattr(emit, "eol", "\n"))


def debug(*objects: object, sep: str = " "):
    if getattr(debug, "enabled", False):
        print(sep.join(map(str, objects)))


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        main(sys.argv[0], *sys.argv[1:])
