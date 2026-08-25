import subprocess
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def get_release_label() -> str:

    """
    Name of the currently checked out release, i.e. the latest git tag
    (e.g. "v0.2.0"). Falls back to "v?.?.?" if this isn't a git checkout
    or has no tags at all.
    """

    try:
        tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd = REPO_DIR, capture_output = True, text = True, check = True, timeout = 2,
        ).stdout.strip()

        return tag or "v?.?.?"

    except (subprocess.CalledProcessError, OSError):
        return "v?.?.?"
