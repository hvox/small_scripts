#!/usr/bin/env python3
"""
SCRIPT_DESCRIPTION

Usage: {script} [OPTIONS] [SOURCE] [TARGET]

Arguments:
    SOURCE - Path to the source file to be converted or to the
             directory where all files are to be converted.
             If not specified, use current directory.
    TARGET - Path where to place generated content.
             Default: beside the source.

Options:
    -h, --help
        Show this screen and exit.
"""

import sys
from contextlib import suppress
from pathlib import Path


SOURCE_SUFFIXES: set[str] = {".txt"}
SUFFIX: str = ".lines"


def convert(source_path: Path, target_path: Path):
    lines = source_path.read_text().splitlines()
    lines = [f"{i}: {line}" for i, line in enumerate(lines)]
    target_path.write_text("".join(line.rstrip() + "\n" for line in lines))


def main(script_name: str, *script_args: str):
    doc = __doc__.format(script=Path(script_name).name)
    args = __import__("docopt").docopt(doc, script_args)
    path = Path(args["SOURCE"] or ".").resolve()
    if not path.is_dir():
        target_path = Path(args["TARGET"] or (str(path) + f".{SUFFIX}")).resolve()
        convert(path, target_path)
        return
    root, dirs, paths = path, [path], []
    target_path = Path(args["TARGET"] or root).resolve()
    for path in (p for dir in dirs for p in dir.iterdir()):
        if path.stem.startswith("."):
            continue
        if path.is_dir():
            dirs.append(path)
        elif path.is_file() and path.suffix in SOURCE_SUFFIXES:
            paths.append(path)
    for path in paths:
        target = path.with_suffix(SUFFIX)
        convert(path, target / target_path.relative_to(root))


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        main(sys.argv[0], *sys.argv[1:])
