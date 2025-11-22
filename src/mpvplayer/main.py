"""Entry point for ``python -m mpvplayer``."""

from __future__ import annotations

import sys

from . import app


def main() -> None:
    """Module entry point used by ``python -m``."""

    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
