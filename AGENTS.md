本文件面向 **AI 协作者 / 未来维护者**，说明本项目的目标、计划架构和编码规范，方便你在不了解全部上下文的情况下，产出风格一致、易维护的代码。

---

## 1. 项目概述

### 1.1 项目目标

本项目是一个基于 **mpv/libmpv + PySide6 + Python 3.13** 的桌面媒体播放器，重点目标：

1. **美观现代的外观**
   
   - 使用 PySide6 + QSS 打造现代化 UI。
   - 支持暗色 / 浅色主题，视觉层级清晰。

2. **常用设置图形化**
   
   - 替代传统写 `mpv.conf` 的方式，把高频设置（解码、渲染、字幕、音频、快捷键等）搬到 GUI 设置界面。
   - 有明确的配置 schema 和 config manager，支持预设和版本迁移。

3. **针对纯音频文件的友好界面**
   
   - 为音乐、有声读物提供**独立的音频模式窗口**：
     - 显示封面、章节、有声书信息。
     - 可以作为“打开就听”的简洁播放器，不追求 foobar/musicbee 那种全库管理。

4. **最终产物为可执行程序**
   
   - 可通过 PyInstaller/Nuitka 等打包为单个 exe。
   - 支持在系统中设置为默认播放器，关联常见音/视频文件类型（双击文件调用本播放器）。

---

## 2. 目录结构与架构（规划）

本项目采用 **“src layout + 包结构”**。默认结构如下：

```text
project-root/
├─ pyproject.toml
├─ README.md
├─ AGENTS.md                # 本文件
├─ src/
│  └─ mpvplayer/
│     ├─ __init__.py
│     ├─ main.py            # 程序入口
│     ├─ app.py             # QApplication 封装、全局初始化
│     ├─ core/              # 与 UI 无关的逻辑层
│     │  ├─ config/
│     │  │  ├─ __init__.py
│     │  │  ├─ schema.py    # 配置项定义（结构、默认值、范围）
│     │  │  ├─ manager.py   # 配置读写、合并默认值、迁移
│     │  │  └─ presets.py   # 预设（观影模式、音乐模式等）
│     │  ├─ mpv/
│     │  │  ├─ __init__.py
│     │  │  ├─ client.py    # libmpv 底层封装（命令/属性/事件）
│     │  │  ├─ player.py    # 上层播放器接口（play/pause/seek...）
│     │  │  └─ profiles.py  # mpv 参数 <-> 配置项 映射
│     │  ├─ models/         # 数据模型（播放状态/播放列表/元数据）
│     │  ├─ paths.py        # 配置/缓存/日志路径
│     │  ├─ logger.py       # 日志初始化
│     │  └─ utils.py
│     ├─ ui/                # 所有 PySide6 UI 相关
│     │  ├─ themes/         # qss 主题
│     │  ├─ windows/        # 主窗口、设置窗口等
│     │  ├─ widgets/        # 可复用控件（播放控制条、封面视图等）
│     │  └─ layout/         # 复杂布局（可选）
│     ├─ features/          # 按功能划分模块（audio_mode、history 等）
│     └─ i18n/              # 国际化（可选）
└─ tests/
   └─ ...
```

> **协作者注意：** 新增模块时优先按照上述分层归类，不要在 `main.py` 或顶层乱塞业务逻辑。

---

## 3. 分层职责说明

### 3.1 `main.py` / `app.py`

* `main.py`
  
  * 只负责：解析命令行参数（文件路径等）、创建 `QApplication`、构造主窗口并运行事件循环。
  
  * 允许的逻辑：
    
    * 读取 `sys.argv`，确定是否要立即打开某个文件。
    * 调用 `app.create_main_window()` 或类似函数。

* `app.py`
  
  * 封装：
    
    * 日志初始化
    * 配置加载
    * 主题设置
    * 主窗口创建工厂方法
  
  * 可以在这里完成“依赖注入”（例如把 `MpvPlayer`、`ConfigManager` 实例传入主窗口）。

> 目标：**入口尽可能薄**，方便打包和测试。

---

### 3.2 `core/`：与 UI 完全解耦

主要面向逻辑和数据：

* `core/mpv/client.py`
  
  * 与 **libmpv** 的最底层交互：
    
    * 初始化 `MPV` 实例（含 `wid` / `vo` / `hwdec` 等选项）。
    * 封装 `command()` / `set_property()` / `get_property()`。
    * 处理 mpv 事件循环（property observer / event 回调），但不要直接触碰 Qt。

* `core/mpv/player.py`
  
  * 提供一个更“人性化”的播放器接口，例如：
    
    * `open_file(path: str)`
    * `play()`, `pause()`, `toggle_pause()`
    * `seek(seconds: float)`, `set_volume(int)`, `set_audio_track(...)`
  
  * 只面向业务语义，不关心 UI 形态（音频模式还是视频模式）。

* `core/config/schema.py`
  
  * 定义所有配置项结构：
    
    * 类型（bool / int / float / enum / str）
    * 合法范围
    * 默认值
  
  * 该 schema 是 UI 生成设置界面的依据。

* `core/config/manager.py`
  
  * 对外提供类型安全的访问接口：
    
    * `get("video.hwdec") -> str`
    * `set("audio.volume", 80)`
  
  * 负责读写磁盘上的配置文件（json/toml/yaml，具体实现时统一）。

* `core/config/presets.py`
  
  * 定义各类预设（如“观影模式”、“音乐模式”、“低功耗模式”）。

* `core/models/`
  
  * `playback_state.py`：播放状态（暂停/播放/进度/当前媒体信息）。
  * `playlist.py`：播放列表模型。
  * `metadata.py`：从文件中提取元数据（标题、专辑、封面、章节）。

> **协作者要求：** 不要在 `core` 下引用任何 PySide6 / Qt 类；如需和 UI 交互，通过更上层或信号机制完成。

---

### 3.3 `ui/`：界面与交互

* `ui/windows/main_window.py`
  
  * 视频模式的主界面：视频画面 + 播放控制条 + 菜单 / 状态栏。

* `ui/windows/audio_window.py`
  
  * 音频模式界面：大封面 + 章节列表 + 播放控制 + 简洁信息栏。
  * 旨在“打开就听”，不要求库管理功能。

* `ui/windows/settings_dialog.py`
  
  * 基于 `core.config.schema` 自动生成表单控件（checkbox/combo/slider）。
  * 通过 `ConfigManager` 实时读取/应用配置。

* `ui/widgets/`
  
  * 复用：播放器控制条、时间轴、封面视图、章节列表等。
  * 尽量保持纯 UI，底层逻辑通过信号和控制器交互。

* `ui/themes/`
  
  * 使用 QSS 管理主题：
    
    * `default.qss` / `dark.qss` / `light.qss`
  
  * 推荐通过一个 `ThemeManager` 统一加载和切换。

> **协作者要求：**
> 
> * 所有 UI 逻辑都通过 Qt 的 signal/slot 与核心逻辑交互。
> * UI 层只管“展示”和“触发动作”，不要直接写复杂业务逻辑。

---

### 3.4 `features/`：按功能组织的“组合层”

* 例如：
  
  * `features/audio_mode/`：处理音频模式下 UI 与 `MpvPlayer` 的交互。
  * `features/history/`：播放历史记录与“继续播放”功能。
  * `features/shortcuts/`：快捷键绑定与映射逻辑。
  * `features/tray/`：系统托盘图标。

特征模块通常包含：

* `controller.py`：作为该功能的“协调者”，连接 `core` 与 `ui`。
* `view_model.py`（可选）：存储 UI 所需的状态，避免 UI 自己乱管业务。

---

## 4. 编码规范

### 4.1 语言 & 版本

* **Python 版本**：3.13（避免使用已废弃特性）
* 强烈建议使用 **type hints**（类型标注）+ `mypy` / `pyright` 检查。

示例：

```python
def open_file(self, path: str) -> None:
    ...
```

---

### 4.2 命名规范（PEP 8 基础上略做说明）

* 模块 / 文件：`snake_case.py`

* 包 / 目录：`lower_snake_case`

* 类名：`CamelCase`
  
  * 例如：`MainWindow`, `MpvPlayer`, `ConfigManager`

* 函数 / 方法：`snake_case`
  
  * 例如：`open_file`, `toggle_play_pause`

* 常量：`UPPER_SNAKE_CASE`

* 私有属性：单前导下划线 `_internal_state`

---

### 4.3 文档与注释

**函数/类文档字符串（docstring）要求：**

* 公共 API（核心类、主要方法）必须写 docstring。
* 风格推荐类似 Google 或 numpydoc 之一，统一即可。

示例：

```python
class MpvPlayer:
    """High-level wrapper around libmpv.

    Responsible for loading files, controlling playback, and querying
    playback state. Does not depend on any Qt classes.
    """

    def open_file(self, path: str) -> None:
        """Open and start playing a given media file."""
        ...
```

**行级注释：**

* 避免写“复读机注释”（比如 `# pause the video` 写在 `self.pause()` 上面）。

* 保留注释给：
  
  * 不明显的业务逻辑；
  * mpv/Qt 的“坑点”（比如某些平台差异、必须的调用顺序）。

---

### 4.4 类型与错误处理

* 对外公开的接口尽量有明确类型标注，不使用 `Any`。
* 避免在底层类里使用“裸 `except:`”；捕获时尽量指定异常类型。
* 对用户输入/文件路径要做基本检查（是否存在/是否可读）并通过 UI 反馈错误信息。

---

### 4.5 AI 生成代码的要求（面向 AGENT）

当你作为 AI 协作者生成代码时，请遵守：

1. **保持与现有结构一致**
   
   * 如果要新增类/函数，优先选择已有模块中合理的位置；
   * 如果需要新模块，遵循上文的分层原则（core/ui/features）。

2. **不要破坏依赖方向**
   
   * `ui` 可以 import `core`，反过来禁止；
   * `features` 可以 import `core` 和 `ui`；
   * `core` 不得 import PySide6/Qt 类。

3. **保持最小惊讶原则**
   
   * 不随意引入新的第三方库（除非明确需要，并在注释中解释原因）；
   * 不写过于“魔法”的元编程（复杂 metaclass、黑魔法装饰器等），以可读性为先。

4. **解释关键设计**
   
   * 对于新增的较大模块/类，请在文件顶部写一段简要说明：
     
     * 这个模块的职责；
     * 它依赖谁，被谁使用；
     * 未来可扩展点（如 TODO）。

5. **测试意识**
   
   * 对 `core` 层新增功能，尽量给出简短的单元测试或至少演示用例；
   * 避免将测试逻辑混入生产代码。

---

### 4.6 Qt / PySide6 相关约定

* 使用 `Signal` / `Slot` 时：
  
  * 自定义 `Signal` 放在类开头，便于查看；
  * 槽函数命名建议以 `on_` 开头，如 `on_play_clicked`。

* UI 更新必须在主线程完成：
  
  * mpv 的事件回调若在非主线程，请通过 Qt 信号转发。

* 资源（icons/fonts/qss）：
  
  * 尽量统一放在 `resources/` 或 `ui/assets/`，必要时使用 Qt `.qrc` 资源系统。
  * UI 代码中不要写死系统绝对路径。

---

## 5. 未来规划（供 AGENT 参考）

在不破坏现有架构的前提下，未来可能增加：

* 播放历史 & 继续播放（`features/history`）
* 播放列表管理（导入/导出 m3u、记住最近播放列表）
* 简单均衡器/音效预设
* 歌词/文本同步（尤其针对有声读物）
* 国际化（i18n：中/英）

在添加这些功能时：

* 尽量通过 `features/` 下新子模块实现；
* 避免在 `main_window.py` 混入太多业务代码，保持主窗口只负责拼装 UI + 调用控制器。

---

如果你是 AI 协作者：
**在开始修改或新增文件前，先判断该改动属于哪个层级（core/ui/features），并在提交/回复中简要说明这次改动的层级和依赖方向。**


