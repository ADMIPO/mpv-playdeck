"""MpvClient 与 MpvPlayer 的基础行为回归测试。"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("PySide6")

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from mpvplayer.core.mpv.client import MpvClient
from mpvplayer.core.mpv.player import MpvPlayer


class DummyMPV:
    """用于隔离 python-mpv 依赖的最小桩实现。"""

    def __init__(self, log_handler=None, ytdl=False) -> None:  # noqa: D401 - 与真实签名保持一致
        self.log_handler = log_handler
        self.ytdl = ytdl
        self.commands: list[tuple[str, ...]] = []
        self.properties: dict[str, Any] = {}
        self.observers: dict[str, list] = {}
        self.events: list[Any] = []
        self.pause = False
        self.terminated = False
        self.wid: int | None = None

    def play(self, path: str) -> None:
        self.commands.append(("play", path))

    def command(self, name: str, *args: object) -> object:
        record = (name, *args)
        self.commands.append(tuple(map(str, record)))
        return record

    def set_property(self, name: str, value: object) -> None:
        self.properties[name] = value
        for callback in self.observers.get(name, []):
            callback(name, value)

    def get_property(self, name: str) -> object:
        if name in self.properties:
            return self.properties[name]
        attr_name = name.replace("-", "_")
        if hasattr(self, attr_name):
            return getattr(self, attr_name)
        return None

    def observe_property(self, name: str, callback) -> None:
        self.observers.setdefault(name, []).append(callback)

    def unobserve_property(self, name: str, callback) -> None:
        callbacks = self.observers.get(name, [])
        if callback in callbacks:
            callbacks.remove(callback)

    def wait_for_event(self, timeout: float) -> object | None:  # noqa: ARG002 - 与真实签名保持一致
        if self.events:
            return self.events.pop(0)
        return None

    def terminate(self) -> None:
        self.terminated = True


@pytest.fixture(autouse=True)
def _inject_dummy_mpv(monkeypatch):
    """将 ``mpv`` 模块替换为轻量桩，避免真实依赖。"""

    dummy_module = types.SimpleNamespace(MPV=DummyMPV)
    monkeypatch.setitem(sys.modules, "mpv", dummy_module)
    yield
    sys.modules.pop("mpv", None)


def test_client_command_and_property_cycle(tmp_path: Path) -> None:
    media = tmp_path / "sample.mp4"
    media.write_text("dummy")

    client = MpvClient()
    client.load_file(media)
    assert client.get_property("volume") is None

    client.set_property("volume", 50)
    assert client.get_property("volume") == 50

    observed: list[tuple[str, object]] = []

    def on_mute(name: str, value: object) -> None:
        observed.append((name, value))

    client.observe_property("mute", on_mute)
    client.set_property("mute", True)
    client.unobserve_property("mute", on_mute)
    assert observed == [("mute", True)]

    client.command("seek", 10, "absolute")
    mpv_instance: DummyMPV = client._mpv_instance  # type: ignore[assignment]
    assert ("play", str(media)) in mpv_instance.commands
    assert ("seek", "10", "absolute") in mpv_instance.commands


def test_client_event_polling_dispatch() -> None:
    client = MpvClient()
    mpv_instance: DummyMPV = client._mpv_instance  # type: ignore[assignment]
    captured: list[object] = []

    client.add_event_callback(captured.append)
    mpv_instance.events.append({"event": "end-file"})
    client.poll_event(0)

    assert captured == [{"event": "end-file"}]


def test_player_high_level_controls(tmp_path: Path) -> None:
    media = tmp_path / "music.flac"
    media.write_text("audio")

    player = MpvPlayer()
    player.open_file(media)
    player.pause()
    player.play()
    player.seek(12)
    player.seek_relative(-3)
    player.set_volume(30)
    player.set_mute(True)

    mpv_instance: DummyMPV = player.client._mpv_instance  # type: ignore[assignment]
    assert mpv_instance.pause is False
    assert player.is_paused() is False
    assert player.get_duration() is None
    assert player.get_position() is None
    assert ("seek", "12", "absolute") in mpv_instance.commands
    assert ("seek", "-3", "relative") in mpv_instance.commands
    assert mpv_instance.properties["volume"] == 30
    assert mpv_instance.properties["mute"] is True


def test_player_tolerates_unready_properties(monkeypatch, tmp_path: Path) -> None:
    """回归：mpv 属性尚未可用时 ``open_file`` 不应抛出异常。"""

    media = tmp_path / "video.mkv"
    media.write_text("stub")

    player = MpvPlayer()
    mpv_instance: DummyMPV = player.client._mpv_instance  # type: ignore[assignment]

    def flaky_get_property(name: str):
        if name == "duration":
            # 首次访问 duration 时模拟 mpv 尚未准备好返回属性。
            raise AttributeError("duration not ready")
        if name == "pause":
            return False
        if name == "eof-reached":
            return False
        return None

    monkeypatch.setattr(mpv_instance, "get_property", flaky_get_property)

    player.open_file(media)
    assert player.get_state().duration is None

    # 后续轮询应能在属性可用时成功填充。
    monkeypatch.setattr(
        mpv_instance, "get_property", lambda name: 42.0 if name == "duration" else None
    )
    player._poll_playback()

    assert player.get_state().duration == 42.0

