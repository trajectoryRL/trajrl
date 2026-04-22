"""trajrl — skill hub installer for TrajectoryRL.

Single source of truth for the version is the installed distribution
metadata (i.e. ``pyproject.toml``). Do not hard-code the version here.
"""

from importlib.metadata import PackageNotFoundError, version as _dist_version

try:
    __version__ = _dist_version("trajrl")
except PackageNotFoundError:
    # Running from a source checkout without an installed dist (e.g. tests
    # before `pip install -e .`). Fall back to a sentinel so tooling still
    # works; the wheel will always have real metadata.
    __version__ = "0.0.0+unknown"
