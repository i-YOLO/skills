# 生产合同

## 项目文件

`init_project.py` 创建以下唯一来源：

- `production-state.json`：格式、输入指纹、当前阶段、每个闸门、自检与人工记录。
- `script.md`：批准的口播文案。
- `captions.json`：标准 Remotion `Caption[]`，每项至少包含 `text`、`startMs`、`endMs`、`timestampMs`。
- `storyboard.json`：音频时间轴、镜头卡、图层、动作、字幕安全区和转场。
- `assets.json`：每个生成、处理、选中和引用素材的来源与审批状态。

不要维护第二份时间轴或资产清单。设计稿、提示词、预览和审阅证据均链接回上述文件。

## 环境作为前置条件

初始化项目后先运行 `check_environment.py --stage script --project-dir <project-dir>`，并将报告放在 `reviews/environment-<stage>.json`。进入音频、素材、动画和成片阶段前重复检查对应阶段。

- `assets` 只有在当前 Agent 明确确认内置 ImageGen 可用，并以 `--confirm-imagegen` 记录后才可通过。
- `animation` 只有项目 `remotion/node_modules/remotion` 存在后才可通过；预检不会自动执行 `npm install`。
- `audio` 默认要求本地转录器；若用户提供已批准 `Caption[]`，以 `--caption-source approved-captions` 记录替代来源。
- 环境检查返回 `blocked` 或 `needs_agent_confirmation` 时，不得记录该阶段自检通过。

详见 [environment.md](environment.md)。

## 阶段与审批

| 阶段 | 最小输入 | Agent 自检产物 | 人工审批产物 |
| --- | --- | --- | --- |
| `script` | 选题、受众、交付比例 | 文案和节奏报告 | 最终文案 |
| `audio` | 原始口播、批准文案 | FFprobe 报告、校正后的 `Caption[]` | 音频报告和字幕时序 |
| `storyboard` | 锁定音频与字幕 | 分镜、占位 Animatic、素材清单 | 分镜总览 |
| `style` | 批准分镜 | 三张关键定帧 | 风格样张 |
| `assets` | 批准风格和素材清单 | 透明/方向/质量检查、联系表 | 分场素材联系表 |
| `scene_animation` | 批准素材 | 入口/定帧/出口、短预览 | 分场总览 |
| `master` | 批准分场动画 | 流、解码、黑帧、静帧、全片证据 | 成片与最终联系表 |

记录自检：

```bash
python <skill>/scripts/record_gate.py <project-dir> \
  --stage assets --kind self --result pass --report reviews/assets-self-review.md
```

在用户明确批准后记录人工闸门；`--statement` 必须保留用户原话：

```bash
python <skill>/scripts/record_gate.py <project-dir> \
  --stage assets --kind human --result approved --statement "素材通过"
```

记录终审时额外要求：

```bash
python <skill>/scripts/record_gate.py <project-dir> \
  --stage master --kind human --result approved \
  --explicit-final-approval --statement "最终产物检查通过"
```

不得替用户填写批准语句，也不得把对中间产物的评价写入 `master`。

## 输入变更与失效

用下列命令登记已批准输入的文件指纹。哈希发生变化时会自动取消下游人工批准和自检。

```bash
python <skill>/scripts/update_input.py <project-dir> --stage script --path script.md --reason "文案修订"
python <skill>/scripts/update_input.py <project-dir> --stage audio --path audio/narration-master.wav --reason "更换口播"
python <skill>/scripts/update_input.py <project-dir> --stage storyboard --path storyboard.json --reason "调整 S04"
python <skill>/scripts/update_input.py <project-dir> --stage assets --path assets.json --reason "替换素材"
```

- 文案变化：取消音频及其后一切锁。
- 音频变化：取消分镜、风格、素材、动画和成片锁。
- 分镜变化：取消风格、素材、动画和成片锁；局部改动时在人工记录中列出受影响场景。
- 素材变化：取消引用该素材的场景动画与成片锁；若无法可靠确定引用范围，取消全部分场动画锁。
- 格式变化：取消分镜、素材、动画和成片锁。

## 音频处理

保留原始音频，生成 48kHz 工作副本。检查时长、采样率、声道、峰值、爆音、异常静音、漏读和重读。若用户确认口播与批准文案一致，用文案作为文字源；否则先转录并由人工修正错字。实际停顿和语速始终以音频为准。

总帧数使用 `ceil(audioDuration × fps)`。音频与最终视频的允许时长差不超过一帧。
