from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VALIDATOR_PATH = _REPO_ROOT / ".github" / "release" / "validate_release_ref.py"
_VALIDATOR_SPEC = spec_from_file_location("release_ref_validator", _VALIDATOR_PATH)
assert _VALIDATOR_SPEC is not None and _VALIDATOR_SPEC.loader is not None
_VALIDATOR = module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)


def _write_release_files(
    tmp_path: Path,
    *,
    version: str = "0.4.0",
    runtime_version: str = "0.4.0",
    changelog_heading: str = "## [0.4.0] - 2026-10-14",
) -> tuple[Path, Path, Path]:
    version_file = tmp_path / "VERSION"
    version_file.write_text(f"{version}\n", encoding="utf-8")
    runtime_file = tmp_path / "__version__.py"
    runtime_file.write_text(f"__version__ = {runtime_version!r}\n", encoding="utf-8")
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(f"# Changelog\n\n{changelog_heading}\n", encoding="utf-8")
    return version_file, runtime_file, changelog_file


def _validate(tag: str, paths: tuple[Path, Path, Path]) -> None:
    _VALIDATOR.validate_release_ref(tag, *paths)


def test_accepts_matching_numeric_release_tag_and_metadata(tmp_path: Path) -> None:
    _validate("0.4.0", _write_release_files(tmp_path))


@pytest.mark.parametrize("tag", ["v0.4.0", "0.4", "00.4.0", "0.4.0-rc1"])
def test_rejects_non_release_tag_formats(tmp_path: Path, tag: str) -> None:
    with pytest.raises(ValueError, match="numeric X.Y.Z"):
        _validate(tag, _write_release_files(tmp_path))


def test_rejects_tag_that_does_not_match_package_version(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not match VERSION"):
        _validate("0.4.1", _write_release_files(tmp_path))


def test_rejects_runtime_version_mismatch(tmp_path: Path) -> None:
    paths = _write_release_files(tmp_path, runtime_version="0.3.0")
    with pytest.raises(ValueError, match="does not match .*__version__"):
        _validate("0.4.0", paths)


def test_requires_dated_changelog_heading(tmp_path: Path) -> None:
    paths = _write_release_files(tmp_path, changelog_heading="## [Unreleased]")
    with pytest.raises(ValueError, match="dated heading"):
        _validate("0.4.0", paths)
