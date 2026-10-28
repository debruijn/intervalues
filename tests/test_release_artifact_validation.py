from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from zipfile import ZipFile

import pytest

import intervalues


_REPO_ROOT = Path(__file__).resolve().parents[1]
_RELEASE_VERSION = (_REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
_VALIDATOR_PATH = _REPO_ROOT / ".github" / "release" / "validate_artifacts.py"
_VALIDATOR_SPEC = spec_from_file_location("release_artifact_validator", _VALIDATOR_PATH)
assert _VALIDATOR_SPEC is not None and _VALIDATOR_SPEC.loader is not None
_VALIDATOR = module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)


def test_runtime_version_matches_release_version() -> None:
    assert intervalues.__version__ == _RELEASE_VERSION


@pytest.mark.parametrize(
    ("python_tag", "abi_tag", "platform_tags", "expected_target"),
    [
        ("cp312", "abi3", "manylinux2014_x86_64", "linux_x86_64"),
        ("cp312", "abi3", "manylinux_2_17_x86_64", "linux_x86_64"),
        (
            "cp312",
            "abi3",
            "manylinux2014_x86_64.manylinux_2_17_x86_64",
            "linux_x86_64",
        ),
        ("cp312", "abi3", "manylinux2014_aarch64", "linux_aarch64"),
        ("cp312", "abi3", "manylinux_2_17_aarch64", "linux_aarch64"),
        ("cp312", "abi3", "macosx_10_13_x86_64", "macos_x86_64"),
        ("cp312", "abi3", "macosx_11_0_arm64", "macos_arm64"),
        ("cp312", "abi3", "win_amd64", "windows_x86_64"),
        ("pp312", "pypy312_pp80", "manylinux_2_28_x86_64", "pypy_linux_x86_64"),
        ("py3", "none", "any", "python_fallback"),
    ],
)
def test_accepts_expected_wheel_targets(
    python_tag: str,
    abi_tag: str,
    platform_tags: str,
    expected_target: str,
) -> None:
    assert (
        _VALIDATOR._target_for_wheel(python_tag, abi_tag, platform_tags)
        == expected_target
    )


@pytest.mark.parametrize(
    ("python_tag", "abi_tag", "platform_tags"),
    [
        ("cp312", "abi3", "manylinux_2_28_x86_64"),
        ("cp312", "abi3", "manylinux2014_s390x"),
        ("cp312", "abi3", "macosx_10_12_x86_64"),
        ("cp312", "abi3", "macosx_11_0_x86_64"),
        ("cp312", "abi3", "win32"),
        ("pp312", "pypy312_pp80", "manylinux2014_x86_64"),
        ("py3", "none", "linux_x86_64"),
        ("cp311", "abi3", "manylinux2014_x86_64"),
    ],
)
def test_rejects_unapproved_wheel_targets(
    python_tag: str,
    abi_tag: str,
    platform_tags: str,
) -> None:
    assert _VALIDATOR._target_for_wheel(python_tag, abi_tag, platform_tags) is None


def _write_test_wheel(
    wheel_dir: Path,
    filename: str,
    tags: list[str],
    *,
    has_extension: bool,
    extension_suffix: str = ".so",
    metadata_line_ending: str = "\n",
) -> None:
    version = _RELEASE_VERSION
    dist_info = f"intervalues-{version}.dist-info"
    with ZipFile(wheel_dir / filename, "w") as archive:
        archive.writestr("intervalues/py.typed", "")
        archive.writestr(
            f"{dist_info}/METADATA",
            metadata_line_ending.join(
                ("Name: intervalues", f"Version: {version}", "")
            ),
        )
        archive.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\n"
            + "".join(f"Tag: {tag}\n" for tag in tags),
        )
        if has_extension:
            archive.writestr(
                f"intervalues/intervalues_pyrust{extension_suffix}",
                b"native",
            )


def _write_supported_wheels(wheel_dir: Path) -> None:
    wheels = [
        ("cp312", "abi3", "manylinux2014_x86_64", ".so"),
        ("cp312", "abi3", "manylinux2014_aarch64", ".so"),
        ("cp312", "abi3", "macosx_10_13_x86_64", ".so"),
        ("cp312", "abi3", "macosx_11_0_arm64", ".so"),
        ("cp312", "abi3", "win_amd64", ".pyd"),
        ("pp312", "pypy312_pp80", "manylinux_2_28_x86_64", ".so"),
    ]
    for python_tag, abi_tag, platform_tag, extension_suffix in wheels:
        _write_test_wheel(
            wheel_dir,
            f"intervalues-{_RELEASE_VERSION}-{python_tag}-{abi_tag}-{platform_tag}.whl",
            [f"{python_tag}-{abi_tag}-{platform_tag}"],
            has_extension=True,
            extension_suffix=extension_suffix,
            metadata_line_ending="\r\n" if platform_tag == "win_amd64" else "\n",
        )
    _write_test_wheel(
        wheel_dir,
        f"intervalues-{_RELEASE_VERSION}-py3-none-any.whl",
        ["py3-none-any"],
        has_extension=False,
    )


def test_validates_wheels_for_all_supported_targets(tmp_path: Path) -> None:
    _write_supported_wheels(tmp_path)
    _VALIDATOR.validate_wheels(tmp_path, _RELEASE_VERSION)


def test_rejects_native_extension_in_python_fallback(tmp_path: Path) -> None:
    _write_supported_wheels(tmp_path)
    fallback_filename = f"intervalues-{_RELEASE_VERSION}-py3-none-any.whl"
    (tmp_path / fallback_filename).unlink()
    _write_test_wheel(
        tmp_path,
        fallback_filename,
        ["py3-none-any"],
        has_extension=True,
        extension_suffix=".pyd",
    )

    with pytest.raises(
        ValueError,
        match="pure-Python fallback must not contain native binaries",
    ):
        _VALIDATOR.validate_wheels(tmp_path, _RELEASE_VERSION)
