"""配置读写与合并逻辑。

该模块负责从磁盘加载配置、保存用户修改，并在缺失字段时自动补全默认值。
同时预留版本迁移钩子，方便未来升级配置结构时平滑处理旧数据。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .schema import AppConfig, CONFIG_VERSION

MigrationHook = Callable[[Dict[str, Any]], Dict[str, Any]]


class ConfigManager:
    """管理应用配置的加载、保存与默认值合并。"""

    def __init__(self, config_path: Path | str, *, migration_hook: Optional[MigrationHook] = None) -> None:
        self.config_path = Path(config_path)
        self._migration_hook = migration_hook

    def load(self) -> AppConfig:
        """读取配置文件并返回合并默认值后的 :class:`AppConfig`。"""

        if not self.config_path.exists():
            return AppConfig()

        raw_data = self._read_raw()
        migrated_data = self._run_migration(raw_data)
        config = AppConfig.from_dict(migrated_data)
        config.validate()
        return config

    def save(self, config: AppConfig) -> None:
        """将配置写入磁盘，自动创建父目录。"""

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as fp:
            json.dump(config.to_dict(), fp, ensure_ascii=False, indent=2)

    def update_and_save(self, overrides: Dict[str, Any]) -> AppConfig:
        """在现有配置上应用覆盖项并保存。"""

        current = self.load()
        new_config = current.apply_overrides(overrides)
        self.save(new_config)
        return new_config

    def _run_migration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行可选的版本迁移。"""

        if self._migration_hook is None:
            return data

        migrated = self._migration_hook(data)
        if not isinstance(migrated, dict):
            raise TypeError("迁移钩子必须返回字典数据")
        if migrated.get("version", data.get("version", CONFIG_VERSION)) < CONFIG_VERSION:
            migrated["version"] = CONFIG_VERSION
        return migrated

    def _read_raw(self) -> Dict[str, Any]:
        """读取原始 JSON 内容。"""

        with self.config_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
