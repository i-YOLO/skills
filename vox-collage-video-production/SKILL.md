---
name: vox-collage-video-production
description: Produce an original, review-gated Chinese voiceover video in a Vox-inspired editorial paper-collage style. Use when the user wants to turn approved Chinese narration and audio into a 16:9, 9:16, 1:1, 4:5, or custom-aspect collage video with ImageGen asset generation, Remotion animation, captions, visual QA, and human approvals.
---

# VOX 拼贴口播视频生产

将口播制作成可审核、可返工、可交付的纸艺拼贴视频。先锁定事实与音频，再锁定镜头和分层素材，最后制作动画；不要把字幕、文字卡或单张海报误当作画面。

## 首次沟通：先锁格式

在写文案或生成任何素材前，询问并记录交付格式。不要自行假定横版。

| 预设 | 默认像素 | 常用场景 |
| --- | --- | --- |
| `16:9` | `1920×1080` | 横版平台、演示视频 |
| `9:16` | `1080×1920` | 短视频平台 |
| `1:1` | `1080×1080` | 方图社媒视频 |
| `4:5` | `1080×1350` | 信息流视频 |

允许用户给出自定义宽高和帧率。确认比例、分辨率、帧率与交付平台后，运行：

```bash
python <skill>/scripts/init_project.py <project-dir> --title "<title>" --format 9:16
```

自定义尺寸使用 `--width`、`--height`，帧率使用 `--fps`。脚本会生成状态文件、审核目录、素材目录和最小 Remotion 工程。比例、分辨率、帧率或音频一旦改变，运行 `update_input.py` 使相应下游锁失效；不得只裁切原有构图。

## 环境预检：每阶段先验证

安装 Skill 不会安装 Python、FFmpeg、转录器、Node、Remotion 或 ImageGen。开始项目后先运行当前阶段的预检；缺失项必须阻断并报告，不能静默安装或降级。

```bash
python <skill>/scripts/check_environment.py --stage script --project-dir <project-dir> --json-out reviews/environment-script.json
python <skill>/scripts/check_environment.py --stage audio --project-dir <project-dir> --caption-source local-asr --json-out reviews/environment-audio.json
python <skill>/scripts/check_environment.py --stage assets --project-dir <project-dir> --confirm-imagegen --json-out reviews/environment-assets.json
python <skill>/scripts/check_environment.py --stage animation --project-dir <project-dir> --json-out reviews/environment-animation.json
python <skill>/scripts/check_environment.py --stage master --project-dir <project-dir> --json-out reviews/environment-master.json
```

`--confirm-imagegen` 只能在 Agent 已确认当前线程具备内置 `$imagegen` 时使用；shell 无法自行探测该能力。若人工已提供审批过的 `Caption[]`，音频阶段改用 `--caption-source approved-captions`。环境结果会写入项目状态；素材、动画和成片关卡只接受 `pass`。完整依赖表与缺失处理见 [environment.md](references/environment.md)。

## 生产闸门

每个阶段都遵循：**Agent 自检 → 展示可审阅产物 → 人工明确批准 → 记录闸门**。未获批准时，停在当前阶段并按反馈返工。用 `record_gate.py` 记录自检、人工原话和批准状态。

1. **文案**：提供口语化文案；检查主题钩子、逻辑衔接、重复、真实性、节奏和预计时长。文案改动使音频及后续失效。
2. **音频与字幕时间轴**：保存原音频并生成 48kHz 工作副本；用 FFprobe 检查流、峰值、异常静音和时长。以批准文案或人工校对的转录生成逐词/逐句时间轴和 Remotion `Caption[]`；不拉伸语速、不自动删句。
3. **分镜、素材设计、风格样张**：按真实音频语义和停顿分场。每场先写镜头卡、交互、分层素材与音画触发点，再用占位 Animatic 和三张关键样张审核；禁止先生成大量正式图片。
4. **分层素材**：在人工批准的清单内使用 `$imagegen`。对彼此独立移动或跨场复用的对象分别生成；默认每项只生成一张，最多并行三项。只在自检失败或用户要求时，进行一次针对性重生成。
5. **Remotion 分场动画**：先做静止终画面，再从终态反推入场。使用帧驱动、显式缓动、`Sequence`、`interpolate()` 和稳定种子；已安装版本支持时对预加载序列使用 `premountFor`。禁止 CSS 动画、墙钟时间和不稳定随机数。每场输出入口、定帧、出口和 5–12 秒预览。
6. **完整成片**：仅在分场动画批准后渲染对应比例的 H.264 MP4 + AAC。运行成片审计并检查全尺寸和缩略尺寸联系表。
7. **最终人工确认**：只有人工明确表达“最终成片/最终产物已检查并通过”的语义，例如“成片通过”“最终产物检查通过”，才可用 `record_gate.py --explicit-final-approval` 记录完成。一般性的“可以”“没问题”不是终审。

阅读 [production-contract.md](references/production-contract.md) 获取阶段输入、输出、失效规则和审批记录格式。

## 先设计镜头，再生成素材

每场在 `storyboard.json` 写完整镜头卡：

- 时间码、对应口播、知识变化、单一视觉命题和焦点顺序。
- 主体尺度、朝向、共同落点或刻意悬置、遮挡顺序、字幕安全区和转场锚点。
- 核心素材、交互素材、载体、辅助素材、前景遮挡物、背景与代码原生元素。
- 每个图层的最终构图区、层级、入场/停留/退出动作、口播触发词、目标帧和允许遮挡关系。

阅读 [asset-contract.md](references/asset-contract.md)。它定义素材类型、字段、同屏焦点上限、素材碰撞规则和反 PPT 约束。

每个镜头必须揭示、组装、比较、变形、检查或解决某件事；不能用名词卡片轮播代替理解。排比句按词组逐项进场，不能在第一拍把所有素材塞进画面。

## ImageGen 素材规则

默认使用内置 `$imagegen`，不调用 CLI 或 API。为每个独立素材单独调用；用最多三项并发队列提高效率，但每个任务必须有独立提示词、素材 ID 与审核记录。

- 人物、手、机器、纸片、档案图、照片、前景遮挡物分别生成；生成位图不含中文、数字、Logo、水印、UI 或图表文字。
- 简单不透明主体要求纯绿幕或洋红幕，用 ImageGen 的本地抠图流程得到 PNG，并检查透明角、毛边、方向、肢体和重复物体。
- 头发、烟雾、玻璃、液体等复杂对象优先作为整块画面或遮罩；未获用户同意不得切换到 CLI 原生透明模式。
- 把选中的项目素材复制到项目目录，不得让 Remotion 直接引用 `$CODEX_HOME/generated_images`。

使用 [imagegen-prompts.md](references/imagegen-prompts.md) 中的统一风格前缀和按类型模板；阅读 [review-checklist.md](references/review-checklist.md) 后再提交素材联系表。

## 动画、字幕与成片

从 `assets.json` 与 `storyboard.json` 驱动 Remotion。模板位于 `assets/remotion-template/`，初始化时复制到项目中；它提供格式自适应画布、音频、标准字幕层、分层图片渲染和确定性入场骨架。镜头仍须按批准分镜改写，不能把模板布局当成最终画面。

- 字幕独立于场景标题，最多两行，严格留在比例专属安全区。
- 核心视觉动作应在对应口播词的 ±3 帧内触发；允许动作在触发后自然完成，但不能明显抢拍或拖拍。
- 默认同屏仅 1 个主焦点与最多 2 个次焦点。除非分镜明确“谁遮挡谁、为什么遮挡”，否则禁止重叠。
- 使用纸艺动词：滑入、揭开、折页、转轴、落下、盖章、遮罩展开、浅景深视差和克制推镜。背景应安静，主焦点先落位，次焦点后进入。
- 使用代码绘制中文、数字、标签、图表和字幕；不要依赖生成图片中的文字。

阅读 [remotion-contract.md](references/remotion-contract.md)，然后运行：

```bash
python <skill>/scripts/validate_project.py <project-dir> --stage pre-animation
python <skill>/scripts/audit_assets.py <project-dir>
python <skill>/scripts/build_contact_sheet.py <project-dir> --output <project-dir>/assets/review/overview.png
python <skill>/scripts/audit_master.py <project-dir> --video <master.mp4>
```

严格执行 [review-checklist.md](references/review-checklist.md)。工具通过只证明结构和媒体流合格；联系表、播放预览和人工批准才证明画面成立。
