"""配置项数据结构定义与校验逻辑。

本模块仅包含与配置相关的数据模型，不依赖 Qt。提供的 dataclass
负责默认值、类型约束与范围校验，供 :mod:`mpvplayer.core.config.manager`
在读写配置文件时复用。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Mapping, Optional

CONFIG_VERSION = 1


def _coerce_bool(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise TypeError(f"{name} 应为布尔值")


def _coerce_int(value: Any, name: str, *, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} 不能是布尔值")
    if isinstance(value, int):
        if min_value is not None and value < min_value:
            raise ValueError(f"{name} 最小值为 {min_value}")
        if max_value is not None and value > max_value:
            raise ValueError(f"{name} 最大值为 {max_value}")
        return value
    raise TypeError(f"{name} 应为整数")


def _coerce_float(value: Any, name: str, *, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = float(value)
        if min_value is not None and value < min_value:
            raise ValueError(f"{name} 最小值为 {min_value}")
        if max_value is not None and value > max_value:
            raise ValueError(f"{name} 最大值为 {max_value}")
        return value
    raise TypeError(f"{name} 应为数字类型")


def _coerce_str(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise TypeError(f"{name} 应为字符串或 None")


def _validate_choice(value: str, choices: tuple[str, ...], name: str) -> str:
    if value not in choices:
        raise ValueError(f"{name} 仅支持 {choices}")
    return value


@dataclass
class PlaybackConfig:
    """播放相关配置。"""

    start_paused: bool = False
    loop_mode: str = "none"
    speed: float = 1.0
    hwdec: bool = True

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PlaybackConfig":
        start_paused = _coerce_bool(data.get("start_paused", False), "start_paused")
        loop_mode_raw = data.get("loop_mode", "none")
        if not isinstance(loop_mode_raw, str):
            raise TypeError("loop_mode 应为字符串")
        loop_mode = _validate_choice(loop_mode_raw, ("none", "file", "playlist"), "loop_mode")
        speed = _coerce_float(data.get("speed", 1.0), "speed", min_value=0.25, max_value=4.0)
        hwdec = _coerce_bool(data.get("hwdec", True), "hwdec")
        return cls(start_paused=start_paused, loop_mode=loop_mode, speed=speed, hwdec=hwdec)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_paused": self.start_paused,
            "loop_mode": self.loop_mode,
            "speed": self.speed,
            "hwdec": self.hwdec,
        }


@dataclass
class SubtitleConfig:
    """字幕显示相关配置。"""

    enabled: bool = True
    default_language: Optional[str] = None
    font_size: int = 36
    encoding: str = "utf-8"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SubtitleConfig":
        enabled = _coerce_bool(data.get("enabled", True), "enabled")
        default_language = _coerce_str(data.get("default_language", None), "default_language")
        font_size = _coerce_int(data.get("font_size", 36), "font_size", min_value=8, max_value=96)
        encoding_raw = data.get("encoding", "utf-8")
        if not isinstance(encoding_raw, str):
            raise TypeError("encoding 应为字符串")
        return cls(enabled=enabled, default_language=default_language, font_size=font_size, encoding=encoding_raw)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "default_language": self.default_language,
            "font_size": self.font_size,
            "encoding": self.encoding,
        }


@dataclass
class AudioConfig:
    """音频输出相关配置。"""

    volume: int = 80
    mute: bool = False
    audio_device: Optional[str] = None
    normalize: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AudioConfig":
        volume = _coerce_int(data.get("volume", 80), "volume", min_value=0, max_value=130)
        mute = _coerce_bool(data.get("mute", False), "mute")
        audio_device = _coerce_str(data.get("audio_device", None), "audio_device")
        normalize = _coerce_bool(data.get("normalize", False), "normalize")
        return cls(volume=volume, mute=mute, audio_device=audio_device, normalize=normalize)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "volume": self.volume,
            "mute": self.mute,
            "audio_device": self.audio_device,
            "normalize": self.normalize,
        }


@dataclass
class VideoConfig:
    """画面相关配置。"""

    brightness: int = 0
    contrast: int = 0
    scaler: str = "auto"
    deinterlace: bool = True

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VideoConfig":
        brightness = _coerce_int(data.get("brightness", 0), "brightness", min_value=-100, max_value=100)
        contrast = _coerce_int(data.get("contrast", 0), "contrast", min_value=-100, max_value=100)
        scaler_raw = data.get("scaler", "auto")
        if not isinstance(scaler_raw, str):
            raise TypeError("scaler 应为字符串")
        deinterlace = _coerce_bool(data.get("deinterlace", True), "deinterlace")
        return cls(brightness=brightness, contrast=contrast, scaler=scaler_raw, deinterlace=deinterlace)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brightness": self.brightness,
            "contrast": self.contrast,
            "scaler": self.scaler,
            "deinterlace": self.deinterlace,
        }


@dataclass
class AppConfig:
    """顶层配置对象，聚合各配置段。"""

    version: int = CONFIG_VERSION
    playback: PlaybackConfig = field(default_factory=PlaybackConfig)
    subtitle: SubtitleConfig = field(default_factory=SubtitleConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    video: VideoConfig = field(default_factory=VideoConfig)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AppConfig":
        version_raw = data.get("version", CONFIG_VERSION)
        version = _coerce_int(version_raw, "version", min_value=1)
        playback = PlaybackConfig.from_dict(data.get("playback", {}))
        subtitle = SubtitleConfig.from_dict(data.get("subtitle", {}))
        audio = AudioConfig.from_dict(data.get("audio", {}))
        video = VideoConfig.from_dict(data.get("video", {}))
        return cls(version=version, playback=playback, subtitle=subtitle, audio=audio, video=video)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "playback": self.playback.to_dict(),
            "subtitle": self.subtitle.to_dict(),
            "audio": self.audio.to_dict(),
            "video": self.video.to_dict(),
        }

    def apply_overrides(self, overrides: Mapping[str, Any]) -> "AppConfig":
        """基于当前配置应用覆盖项，返回新实例。"""

        def merge_section(current, section_name):
            section_data = overrides.get(section_name, {}) if isinstance(overrides, Mapping) else {}
            if not isinstance(section_data, Mapping):
                raise TypeError(f"{section_name} 覆盖值必须是映射类型")
            return type(current).from_dict({**current.to_dict(), **section_data})

        return replace(
            self,
            playback=merge_section(self.playback, "playback"),
            subtitle=merge_section(self.subtitle, "subtitle"),
            audio=merge_section(self.audio, "audio"),
            video=merge_section(self.video, "video"),
            version=_coerce_int(overrides.get("version", self.version), "version", min_value=1),
        )

    def validate(self) -> None:
        """触发各段的校验（依赖 dataclass 构造时的检查）。"""

        # dataclass 生成时已经完成校验，此处主要保留接口便于未来扩展。
        _ = self.to_dict()
