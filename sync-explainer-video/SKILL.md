---
name: sync-explainer-video
description: 将知识讲解、教学、技术原理、数据可视化和产品演示动画与真实口播音频逐词同步，并修复同步、转场、可读性和媒体参数问题。用于已有静音动画、Manim/Remotion 项目或成片加入口播；使用 Faster-Whisper 建立词级时间轴、识别停顿/重复/未朗读内容、给出分镜级改动方案并验收交付。当用户提到“sync-explainer-video”“声画同步”“逐词对齐”“动画提前/滞后”或要验收口播动画时使用。
---

# Sync Explainer Video：口播声画同步与验收

使用真实口播建立时间轴，再调整动画。不要按字数平均估时，也不要在没有真实音频和词级证据时声称已经同步。

## 何时使用

- 已有 `madem` 制作的静音动画，需要录制口播后同步。
- 已有 Manim/Remotion 项目或成片，需要修复元素提前、滞后、闪退、硬切或长静止。
- 需要检查最终视频与参考音频的同步误差、转场、文字可读性、解码和媒体规格。

若还没有静音动画，先使用 `$madem` 制作并审核静音版本；本 Skill 不用文字稿伪造同步结果。

## 前置检查

运行：

```bash
python scripts/doctor.py --project <project-dir> --model large-v3
```

缺 Faster-Whisper、Manim、FFmpeg/ffprobe、浏览器、字体、模型或项目锁文件时，只报告缺项。只有用户明确授权后才运行 `$madem` 的 `bootstrap_runtime.sh --install`。

使用隔离运行时转录：

```bash
RUNTIME=/Users/shike/.codex/runtimes/video-skills-py311
"$RUNTIME/bin/python" scripts/transcribe_words.py \
  --audio <voiceover.wav> --merge-into <project-dir/timeline.json>
```

默认模型为 `large-v3`、语言为中文、CPU `int8`。模型首次下载前告知用户下载需求；不要改用普通 Whisper 作为“已通过”同步的替代。

## 同步流程

1. 使用 `transcribe_words.py` 生成真实 `words`、`pauses` 和转录元数据；保留原始时间戳。
2. 使用 `transcript_compare.py` 对比逐字稿和真实转录，标记可能的停顿、重复、口误和未朗读内容；把不确定项交给用户或人工回听确认。
3. 为每个分镜补齐 `audio_start` 和 `audio_end`，使其对应实际解释该概念的语音区间；运行 `plan_sync.py` 生成分镜级同步方案。
4. 单个场景音频与静音动画差值在 `±20%` 内时，允许调整停留、转场和动作节奏。若动作变得不自然，仍需补画面。
5. 音频较长且超阈值时，增加有讲解价值的卡片、素材或镜头；音频较短且超阈值时，压缩或移除非关键画面。不要靠明显慢放、空转或长静止凑时长。
6. 先补齐 `visual_actions`：登记每个有意义的标题、卡片、标签、节点、连线、高亮和 CTA 的场景、类型、概念归属、展示截止与是否需要同步。为每个需要同步的动作建立一条严格 `sync_events` 语义事件。
7. 按“词位出现 → 词后完成 → 后续解释继续推进”修改动画。排比、流程和循环必须按口播语序逐项展开，不能整页在场景开头一次性播完后静止等待。
8. 仅当短句临近转场会闪现时，才建立 `prelude_events`：容器、轮廓或弱化标签可提前最多 `0.75s`；完整文案、关键词和高亮仍在对应词位出现。已有专页详解的概念不得在前一页以完整卡片重复展开。
9. 修改 Remotion/Manim 项目或成片后重渲染，先运行 `audit_action_timing.py`，再运行 `validate_sync.py`。同步通过后，交给 `$madem` 以已确认文案生成字幕并加入默认 BGM；BGM 不参与转录、词级对齐或动作锚点计算。

```bash
python scripts/audit_action_timing.py --timeline <timeline.json> --require-manifest --out <action-audit.json>
python scripts/validate_sync.py --timeline <timeline.json> --require-manifest --out <sync-report.json>
```

## 质量闸门

逐个检查：

- 关键词出现前、出现时和出现后；一句话内的动作是否按口播顺序展开。
- 当前概念讲完后是否才进入下一屏；元素是否提前、滞后或过早消失。
- 每段结尾是否留够阅读时间；转场前、中、后是否出现闪帧或硬切。
- 文字、箭头、连线、高亮、图片、视频和技术关系是否正确、可读且不重叠。
- 每个 `sync_required` 动作是否有严格语义锚点；预入场是否只作视觉铺垫、领先不超过 `0.75s`，且短时元素没有在转场前闪退。
- 每个概念是否有唯一详解拥有场景；标题、卡片与下一屏是否在真实语义处接手，而不是为保留旧分镜时长提前堆叠。
- 发布版字幕是否使用已确认文案、真实词级时间与最终帧率；BGM 是否只在同步和字幕画面审核通过后加入，且没有改变已验收视频流。

调用 `$madem` 的 `extract_review_frames.py` 进行每秒基础抽帧和事件帧抽取；允许正常弹入/弹出，但必须修复重叠、越界、模糊、单帧闪烁、不合理布局、播放卡顿、未声明长静止，以及技术示意与口播不一致。

同步误差目标为不超过半帧；超过半帧但不超过一帧为警告，超过一帧为失败。没有严格 `sync_events`、动作清单证据或动作审计失败时，验收状态必须为 `needs-evidence` 或 `fail`，不得标记已同步。

字段定义和修复边界见 [references/sync-schema.md](references/sync-schema.md)。
