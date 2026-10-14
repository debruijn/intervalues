"""Validate the version and changelog metadata for a numeric release tag."""

from __future__ import annotations

import argparse
import ast
from datetime import date
from pathlib import Path
import re


RELEASE_TAG = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)")


def runtime_version(version_file: Path) -> str:
    tree = ast.parse(version_file.read_text(encoding="utf-8"), filename=str(version_file))
    versions = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(versions) != 1:
        raise ValueError(f"Expected one __version__ assignment in {version_file}")
    return versions[0]


def validate_release_ref(
    tag: str,
    version_file: Path = Path("VERSION"),
    runtime_version_file: Path = Path("intervalues/__version__.py"),
    changelog_file: Path = Path("CHANGELOG.md"),
) -> None:
    if RELEASE_TAG.fullmatch(tag) is None:
        raise ValueError(f"Release tag must be numeric X.Y.Z without a prefix: {tag}")

    version = version_file.read_text(encoding="utf-8").strip()
    if version != tag:
        raise ValueError(f"Release tag {tag} does not match VERSION {version}")
    if runtime_version(runtime_version_file) != tag:
        raise ValueError(f"Release tag {tag} does not match {runtime_version_file}")

    changelog = changelog_file.read_text(encoding="utf-8")
    heading = re.search(
        rf"^## \[{re.escape(tag)}\] - (\d{{4}}-\d{{2}}-\d{{2}})$",
        changelog,
        re.MULTILINE,
    )
    if heading is None:
        raise ValueError(f"CHANGELOG.md must contain a dated heading for [{tag}]")
    date.fromisoformat(heading.group(1))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    args = parser.parse_args()
    validate_release_ref(args.tag)
    print(f"Validated release tag {args.tag}")


if __name__ == "__main__":
    main()
