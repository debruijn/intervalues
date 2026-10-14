"""Smoke-test an installed release wheel in cibuildwheel's test environment."""

from __future__ import annotations

import importlib
from importlib.metadata import version as distribution_version
from importlib.util import find_spec
import sys

from intervalues import BaseInterval, __version__, combine_intervals, combine_via_rust


def main() -> None:
    if __version__ != distribution_version("intervalues"):
        raise RuntimeError("The runtime and installed distribution versions do not match")

    extension_spec = find_spec("intervalues_pyrust")
    is_pypy_fallback = (
        sys.implementation.name == "pypy" and sys.version_info[:2] == (3, 10)
    )
    is_unsupported_free_threaded_fallback = (
        sys.implementation.name == "cpython"
        and sys.version_info[:2] < (3, 14)
        and sysconfig_gil_disabled()
    )
    is_python_fallback = (
        is_pypy_fallback or is_unsupported_free_threaded_fallback
    )
    intervals = [BaseInterval(0, 2), BaseInterval(1, 3)]
    python_result = combine_intervals(intervals)
    python_segments = sorted(
        (interval.start, interval.stop, value)
        for interval, value in python_result.items()
    )
    expected = [(0, 1, 1), (1, 2, 2), (2, 3, 1)]
    if python_segments != expected:
        raise RuntimeError("The Python combiner returned an unexpected result")

    if is_python_fallback:
        if extension_spec is not None:
            raise RuntimeError("The Python fallback wheel unexpectedly has the Rust extension")
    else:
        if extension_spec is None:
            raise RuntimeError("This release wheel must include the Rust extension")
        rust_extension = importlib.import_module("intervalues_pyrust")
        if rust_extension.combine_intervals_int([(0, 2, 1), (1, 3, 1)]) != expected:
            raise RuntimeError("The Rust extension returned an unexpected result")
        if combine_via_rust(intervals) != python_result:
            raise RuntimeError("The Rust and Python combiners returned different results")

    if sys.implementation.name == "cpython" and sysconfig_gil_disabled():
        gil_enabled = getattr(sys, "_is_gil_enabled", None)
        if gil_enabled is None or gil_enabled():
            raise RuntimeError("Importing the package enabled the GIL")


def sysconfig_gil_disabled() -> bool:
    import sysconfig

    return bool(sysconfig.get_config_var("Py_GIL_DISABLED"))


if __name__ == "__main__":
    main()
