import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from mpvplayer.core.config.manager import ConfigManager
from mpvplayer.core.config.presets import apply_preset, movie_preset, music_preset
from mpvplayer.core.config.schema import AppConfig, CONFIG_VERSION


def test_load_merges_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"audio": {"volume": 50}}), encoding="utf-8")

    manager = ConfigManager(config_path)
    config = manager.load()

    assert config.audio.volume == 50
    assert config.audio.mute is False
    assert config.playback.loop_mode == "none"
    assert config.subtitle.enabled is True
    assert config.version == CONFIG_VERSION


def test_save_and_reload(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.json"
    manager = ConfigManager(config_path)

    updated = manager.update_and_save({"audio": {"mute": True, "volume": 70}, "playback": {"loop_mode": "file"}})
    assert config_path.exists()

    loaded = manager.load()
    assert loaded.audio.mute is True
    assert loaded.audio.volume == 70
    assert loaded.playback.loop_mode == "file"


def test_migration_hook_invoked(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"version": 0, "audio": {"volume": 40}}), encoding="utf-8")

    def migration(data):
        data = dict(data)
        data["version"] = CONFIG_VERSION
        data.setdefault("subtitle", {})["enabled"] = True
        return data

    manager = ConfigManager(config_path, migration_hook=migration)
    config = manager.load()

    assert config.version == CONFIG_VERSION
    assert config.subtitle.enabled is True


def test_apply_presets(tmp_path: Path) -> None:
    base = AppConfig()

    movie_config = apply_preset(base, movie_preset())
    assert movie_config.subtitle.font_size == 42
    assert movie_config.video.scaler == "ewa_lanczos"

    music_config = apply_preset(base, music_preset())
    assert music_config.subtitle.enabled is False
    assert music_config.playback.loop_mode == "playlist"
    assert music_config.audio.normalize is True
