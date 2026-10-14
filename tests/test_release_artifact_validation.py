from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from zipfile import ZipFile

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[1]
_RELEASE_VERSION = (_REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
_VALIDATOR_PATH = _REPO_ROOT / ".github" / "release" / "validate_artifacts.py"
_VALIDATOR_SPEC = spec_from_file_location("release_artifact_validator", _VALIDATOR_PATH)
assert _VALIDATOR_SPEC is not None and _VALIDATOR_SPEC.loader is not None
_VALIDATOR = module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)


@pytest.mark.parametrize(
    "platform_tags",
    [
        "manylinux2014_x86_64",
        "manylinux_2_17_x86_64",
        "manylinux2014_x86_64.manylinux_2_17_x86_64",
    ],
)
def test_accepts_manylinux2014_equivalent_platform_tags(platform_tags: str) -> None:
    assert _VALIDATOR._has_manylinux2014_platform(platform_tags)


@pytest.mark.parametrize(
    "platform_tags",
    ["manylinux_2_28_x86_64", "manylinux2014_aarch64", "any"],
)
def test_rejects_platforms_outside_manylinux2014_x86_64(platform_tags: str) -> None:
    assert not _VALIDATOR._has_manylinux2014_platform(platform_tags)


def _write_test_wheel(
    wheel_dir: Path,
    filename: str,
    tags: list[str],
    *,
    has_extension: bool,
) -> None:
    version = _RELEASE_VERSION
    dist_info = f"intervalues-{version}.dist-info"
    with ZipFile(wheel_dir / filename, "w") as archive:
        archive.writestr("intervalues/py.typed", "")
        archive.writestr(
            f"{dist_info}/METADATA",
            f"Name: intervalues\nVersion: {version}\n",
        )
        archive.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\n"
            + "".join(f"Tag: {tag}\n" for tag in tags),
        )
        if has_extension:
            archive.writestr("intervalues/intervalues_pyrust.so", b"native")


@pytest.mark.parametrize(
    "platform_tags",
    [
        "manylinux2014_x86_64",
        "manylinux_2_17_x86_64",
        "manylinux2014_x86_64.manylinux_2_17_x86_64",
    ],
)
def test_validates_wheels_with_manylinux2014_equivalent_tags(
    tmp_path: Path,
    platform_tags: str,
) -> None:
    platform_options = platform_tags.split(".")
    _write_test_wheel(
        tmp_path,
        f"intervalues-{_RELEASE_VERSION}-cp310-abi3-{platform_tags}.whl",
        [f"cp310-abi3-{platform}" for platform in platform_options],
        has_extension=True,
    )
    _write_test_wheel(
        tmp_path,
        f"intervalues-{_RELEASE_VERSION}-pp311-pypy311_pp73-{platform_tags}.whl",
        [f"pp311-pypy311_pp73-{platform}" for platform in platform_options],
        has_extension=True,
    )
    _write_test_wheel(
        tmp_path,
        f"intervalues-{_RELEASE_VERSION}-py3-none-any.whl",
        ["py3-none-any"],
        has_extension=False,
    )

    _VALIDATOR.validate_wheels(tmp_path, _RELEASE_VERSION)
