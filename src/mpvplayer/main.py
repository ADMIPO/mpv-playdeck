"""``python -m mpvplayer`` 的入口模块。"""

from __future__ import annotations

import sys

from . import app


def main() -> None:
    """供 ``python -m`` 调用的模块入口。"""

    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
