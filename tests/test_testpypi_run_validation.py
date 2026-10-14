from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "release"
    / "validate_testpypi_run.py"
)
_VALIDATOR_SPEC = spec_from_file_location("testpypi_run_validator", _VALIDATOR_PATH)
assert _VALIDATOR_SPEC is not None and _VALIDATOR_SPEC.loader is not None
_VALIDATOR = module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)


def _successful_run() -> tuple[dict[str, object], list[dict[str, object]]]:
    return (
        {
            "path": ".github/workflows/publish-release.yml@refs/heads/main",
            "event": "workflow_dispatch",
            "head_branch": "main",
            "status": "completed",
            "conclusion": "success",
        },
        [{"name": "Publish validated artifacts to TestPyPI", "conclusion": "success"}],
    )


def test_accepts_successful_testpypi_publish_run() -> None:
    run, jobs = _successful_run()
    _VALIDATOR.validate_run(run, jobs)


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("path", ".github/workflows/other.yml", "did not use"),
        ("event", "push", "manually dispatched"),
        ("head_branch", "development", "from main"),
        ("status", "in_progress", "did not complete"),
        ("conclusion", "failure", "did not complete"),
    ],
)
def test_rejects_invalid_source_workflow_run(
    field: str,
    value: str,
    message: str,
) -> None:
    run, jobs = _successful_run()
    run[field] = value

    with pytest.raises(ValueError, match=message):
        _VALIDATOR.validate_run(run, jobs)


def test_requires_successful_testpypi_publish_job() -> None:
    run, _ = _successful_run()

    with pytest.raises(ValueError, match="did not successfully publish"):
        _VALIDATOR.validate_run(run, [])
