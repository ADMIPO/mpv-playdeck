"""项目通用的简易日志配置。"""

from __future__ import annotations

import logging
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """配置应用的根日志记录器。

    Parameters
    ----------
    level:
        根记录器的日志等级，默认使用 ``logging.INFO``。
    """

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """返回一个已配置的日志记录器实例。

    Parameters
    ----------
    name:
        可选的记录器名称。为 ``None`` 时返回根记录器。
    """

    return logging.getLogger(name)
