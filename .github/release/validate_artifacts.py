"""Validate distribution artifacts produced by the release workflow."""

from __future__ import annotations

import argparse
from email.parser import Parser
from pathlib import Path, PurePosixPath
import tarfile
from typing import NoReturn
from zipfile import ZipFile


LINUX_X86_64_PLATFORMS = frozenset(
    {"manylinux2014_x86_64", "manylinux_2_17_x86_64"}
)
LINUX_AARCH64_PLATFORMS = frozenset(
    {"manylinux2014_aarch64", "manylinux_2_17_aarch64"}
)
PYPY_LINUX_X86_64_PLATFORMS = frozenset({"manylinux_2_28_x86_64"})
EXPECTED_WHEELS = {
    "linux_x86_64": ("cp312", "abi3", True, LINUX_X86_64_PLATFORMS),
    "linux_aarch64": ("cp312", "abi3", True, LINUX_AARCH64_PLATFORMS),
    "macos_x86_64": ("cp312", "abi3", True, frozenset({"macosx_10_13_x86_64"})),
    "macos_arm64": ("cp312", "abi3", True, frozenset({"macosx_11_0_arm64"})),
    "windows_x86_64": ("cp312", "abi3", True, frozenset({"win_amd64"})),
    "pypy_linux_x86_64": ("pp312", "pypy312_pp", True, PYPY_LINUX_X86_64_PLATFORMS),
    "python_fallback": ("py3", "none", False, frozenset({"any"})),
}


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def validate_sdist(dist_dir: Path, version: str) -> None:
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    expected_name = f"intervalues-{version}.tar.gz"
    if [sdist.name for sdist in sdists] != [expected_name]:
        fail(f"Expected exactly {expected_name} in {dist_dir}, found {[p.name for p in sdists]}")

    required_files = {
        "VERSION",
        "setup.cfg",
        "pyproject.toml",
        "rust/Cargo.toml",
        "rust/Cargo.lock",
        "tests/release_wheel_smoke.py",
    }
    root = f"intervalues-{version}/"
    with tarfile.open(sdists[0], "r:gz") as archive:
        members = [member.name for member in archive.getmembers()]
        relative_files = {
            name.removeprefix(root) for name in members if name.startswith(root)
        }
        missing = required_files - relative_files
        if missing:
            fail(f"Source distribution is missing required files: {sorted(missing)}")
        if any("/rust/target/" in f"/{name}" for name in members):
            fail("Source distribution contains generated rust/target files")
        package_info = next(
            (member for member in members if member == f"{root}PKG-INFO"), None
        )
        if package_info is None:
            fail("Source distribution is missing PKG-INFO")
        content = archive.extractfile(package_info)
        if content is None or f"Version: {version}".encode() not in content.read():
            fail(f"Source distribution metadata does not report version {version}")


def _target_for_wheel(
    python_tag: str,
    abi_tag: str,
    platform_tags: str,
) -> str | None:
    for target, (expected_python, expected_abi, _, expected_platforms) in EXPECTED_WHEELS.items():
        if python_tag != expected_python:
            continue
        abi_matches = abi_tag == expected_abi or (
            expected_abi.endswith("_pp") and abi_tag.startswith(expected_abi)
        )
        if abi_matches and expected_platforms.intersection(platform_tags.split(".")):
            return target
    return None


def validate_wheels(wheel_dir: Path, version: str) -> None:
    wheels = sorted(wheel_dir.glob("*.whl"))
    if len(wheels) != len(EXPECTED_WHEELS):
        fail(f"Expected {len(EXPECTED_WHEELS)} wheels, found {[wheel.name for wheel in wheels]}")

    found_targets: set[str] = set()
    for wheel in wheels:
        parts = wheel.stem.split("-")
        if len(parts) != 5:
            fail(f"Unexpected wheel filename format: {wheel.name}")
        distribution, wheel_version, python_tag, abi_tag, platform_tag = parts
        if distribution != "intervalues" or wheel_version != version:
            fail(f"Unexpected distribution or version in wheel filename: {wheel.name}")

        target = _target_for_wheel(python_tag, abi_tag, platform_tag)
        if target is None:
            fail(f"Wheel has an unexpected Python, ABI, or platform tag: {wheel.name}")
        if target in found_targets:
            fail(f"More than one wheel was built for target {target}")
        found_targets.add(target)

        with ZipFile(wheel) as archive:
            names = archive.namelist()
            dist_info = f"intervalues-{version}.dist-info/"
            metadata_name = f"{dist_info}METADATA"
            wheel_metadata_name = f"{dist_info}WHEEL"
            if "intervalues/py.typed" not in names:
                fail(f"{wheel.name} is missing intervalues/py.typed")
            if metadata_name not in names or wheel_metadata_name not in names:
                fail(f"{wheel.name} is missing wheel metadata")

            metadata = Parser().parsestr(archive.read(metadata_name).decode())
            if metadata.get("Name") != "intervalues" or metadata.get("Version") != version:
                fail(f"{wheel.name} metadata does not match version {version}")

            wheel_metadata = archive.read(wheel_metadata_name).decode().splitlines()
            tags = [
                line.removeprefix("Tag: ")
                for line in wheel_metadata
                if line.startswith("Tag: ")
            ]
            expected_python, expected_abi, extension_required, expected_platforms = (
                EXPECTED_WHEELS[target]
            )
            matching_tags = []
            for tag in tags:
                tag_parts = tag.split("-", 2)
                if (
                    len(tag_parts) != 3
                    or tag_parts[0] != expected_python
                    or tag_parts[2] not in expected_platforms
                ):
                    continue
                abi_matches = tag_parts[1] == expected_abi or (
                    expected_abi.endswith("_pp")
                    and tag_parts[1].startswith(expected_abi)
                )
                if abi_matches:
                    matching_tags.append(tag_parts)
            if not matching_tags:
                fail(f"{wheel.name} WHEEL metadata has no matching target tag")

            extension_files = [
                name
                for name in names
                if PurePosixPath(name).name.startswith("intervalues_pyrust.")
                and name.endswith((".so", ".pyd"))
            ]
            has_extension = bool(extension_files)
            if target == "python_fallback" and any(
                name.endswith((".so", ".pyd", ".dll", ".dylib"))
                or archive.read(name).startswith(b"\x7fELF")
                for name in names
            ):
                fail(f"{wheel.name} pure-Python fallback must not contain native binaries")
            if has_extension != extension_required:
                disposition = "must include" if extension_required else "must not include"
                fail(f"{wheel.name} {disposition} the Rust extension")

    if found_targets != set(EXPECTED_WHEELS):
        fail(f"Missing wheel targets: {sorted(set(EXPECTED_WHEELS) - found_targets)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--version-file", type=Path, default=Path("VERSION"))
    args = parser.parse_args()

    version = args.version_file.read_text(encoding="utf-8").strip()
    if not version:
        fail(f"Version file is empty: {args.version_file}")
    validate_sdist(args.dist_dir, version)
    validate_wheels(args.wheel_dir, version)
    print(f"Validated source distribution and {len(EXPECTED_WHEELS)} wheels for {version}")


if __name__ == "__main__":
    main()
