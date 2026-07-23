# 环境预检

安装 Skill 不会自动安装运行时。Agent 必须在首次开始、并在每个需要外部能力的阶段前运行 `check_environment.py`；缺失项是阻断，不得静默安装、降级或跳过。

## 按阶段检查

| 阶段 | 必需条件 | 验证方式 |
| --- | --- | --- |
| `script` | Python 3.10+ | `--stage script` |
| `audio` | Python 3.10+、FFmpeg、FFprobe、本地 Whisper/WhisperX；或人工已审核 `Caption[]` | `--stage audio --caption-source local-asr`；已有字幕时改为 `approved-captions` |
| `assets` | Python 3.10+、Pillow、当前线程可用的内置 ImageGen | Agent 确认工具后，`--stage assets --confirm-imagegen` |
| `animation` | Node.js 18+、npm、项目本地已安装的 Remotion 依赖 | `--stage animation --project-dir <project-dir>` |
| `master` | Python 3.10+、Pillow、FFmpeg、FFprobe | `--stage master --project-dir <project-dir>` |

全量预检：

```bash
python <skill>/scripts/check_environment.py \
  --stage all --project-dir <project-dir> \
  --caption-source local-asr --confirm-imagegen \
  --json-out reviews/environment-all.json
```

全量预检为 `pass` 时，可满足后续各阶段的环境前置条件；任何环境、项目依赖或转录来源改变后，都应改为重新执行受影响的单阶段预检。

`--stage assets` 若不带 `--confirm-imagegen` 会返回 `needs_agent_confirmation`。这是有意设计：内置工具不能由 shell 可靠探测，Agent 必须先在当前线程确认其可用性；不得因为缺失而自动转为 CLI/API。

## 缺失时的处理

- **Python / Pillow**：报告当前解释器与缺失模块；由用户选择项目虚拟环境或安装方式。不要改写系统 Python。
- **FFmpeg / FFprobe**：阻断音频标准化、视频解码和成片交付；由用户安装或提供可用环境。
- **本地转录器**：阻断自动生成时间轴。用户可安装 Whisper/WhisperX，或提供人工校正并批准的 `Caption[]`。
- **Node / npm / Remotion**：阻断动画渲染。确认项目目录正确后，由用户确认是否在 `remotion/` 运行 `npm install`。
- **内置 ImageGen**：阻断素材生成；只能等待具备该工具的 Agent 线程，或在用户明确选择后走另一条经批准的流程。

## 记录与校验

若传入 `--project-dir`，脚本会将检查结果写入 `production-state.json.environment`；若传入 `--json-out`，同时生成可供人工审阅的 JSON 报告。`validate_project.py` 在进入素材、动画与成片关卡前要求相应阶段的环境结果为 `pass`。

Skill 包自身的官方 `quick_validate.py` 额外依赖 Python `PyYAML`，但生产视频流程不依赖它。包内的 `validate_skill.py` 不依赖第三方 YAML 解析器，始终应在交付前运行。
