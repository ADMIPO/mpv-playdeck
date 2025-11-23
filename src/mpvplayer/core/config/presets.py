"""配置预设定义。

提供面向常见使用场景的配置片段，调用方可以直接与
:class:`mpvplayer.core.config.manager.ConfigManager` 结合应用。
"""

from __future__ import annotations

from typing import Dict

from .schema import AppConfig


def movie_preset() -> Dict[str, Dict[str, object]]:
    """观影模式：强调字幕与硬件解码。"""

    return {
        "playback": {"start_paused": False, "loop_mode": "none", "hwdec": True},
        "subtitle": {"enabled": True, "font_size": 42},
        "audio": {"volume": 90, "normalize": False},
        "video": {"deinterlace": True, "scaler": "ewa_lanczos"},
    }


def music_preset() -> Dict[str, Dict[str, object]]:
    """音乐模式：突出音频输出，关闭字幕。"""

    return {
        "playback": {"start_paused": False, "loop_mode": "playlist", "speed": 1.0},
        "subtitle": {"enabled": False},
        "audio": {"volume": 85, "normalize": True},
        "video": {"deinterlace": False},
    }


def apply_preset(base: AppConfig, preset: Dict[str, Dict[str, object]]) -> AppConfig:
    """基于现有配置应用预设并返回新实例。"""

    return base.apply_overrides(preset)
