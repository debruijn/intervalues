"""Prepare a temporary sdist tree for a mandatory Rust-extension wheel build."""

from __future__ import annotations

import argparse
from pathlib import Path


EXTENSION_TABLE = "[[tool.setuptools-rust.ext-modules]]"


def require_rust_extension(source_dir: Path) -> None:
    pyproject = source_dir / "pyproject.toml"
    lines = pyproject.read_text(encoding="utf-8").splitlines(keepends=True)
    in_extension_table = False
    matches = 0

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            in_extension_table = stripped == EXTENSION_TABLE
        if in_extension_table and stripped == "optional = true":
            lines[index] = line.replace("optional = true", "optional = false")
            matches += 1

    if matches != 1:
        raise ValueError(
            f"Expected one optional Rust extension setting in {pyproject}, found {matches}"
        )
    pyproject.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--require-rust-extension", action="store_true")
    parser.add_argument("--free-threaded", action="store_true")
    args = parser.parse_args()

    if args.free_threaded and not args.require_rust_extension:
        parser.error("--free-threaded requires --require-rust-extension")
    if args.require_rust_extension:
        require_rust_extension(args.source_dir)
    if args.free_threaded:
        (args.source_dir / "setup.cfg").unlink()


if __name__ == "__main__":
    main()
