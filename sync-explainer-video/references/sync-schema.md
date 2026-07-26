# 声画同步数据结构与修复边界

## 真实词级时间轴

`timeline.json` 的 `words` 保留 Faster-Whisper 的真实时间。每个对象至少包含 `text`、`start`、`end` 和可用时的 `probability`。`pauses` 记录相邻词间长于阈值的停顿。

不要用文案字数、估计语速或预先设计的动画时间覆盖真实词级时间。

## 分镜映射

每个场景必须有静音动画的 `start`/`end`。同步时补充：

```json
{
  "id": "attention",
  "start": 12.0,
  "end": 20.0,
  "audio_start": 13.1,
  "audio_end": 23.0,
  "hold": false
}
```

`audio_start` 和 `audio_end` 应围住该场景实际解释的语义，不要仅按整个视频的总时长分配。

## 视觉动作清单

在静音分镜阶段登记所有有意义的标题、卡片、标签、节点、连线、高亮和 CTA。收到音频后，动作清单成为同步覆盖率的依据；不要求为纯背景光效、页码等装饰登记。

```json
{
  "visual_actions": [
    {
      "id": "timeline-key-action",
      "scene_id": "frame-anchor",
      "label": "关键动作",
      "element_type": "title",
      "sync_required": true,
      "sync_event_id": "action-timeline-key-action",
      "min_visible_seconds": 1.0,
      "concept_id": "word-timed-key-action",
      "concept_role": "owner"
    }
  ]
}
```

- `element_type` 使用 `card`、`label`、`node`、`title`、`highlight`、`cta` 或 `connection`。
- `sync_required: true` 的动作必须有一条语义同步事件；`order` 可选，用于显式检查排比、流程和循环的口播顺序。
- `visible_until` 可覆盖场景结尾；卡片、标签、节点、标题、高亮和 CTA 默认至少需要 `1.0s` 的可见时长，或使用合规预入场。
- 一个 `concept_id` 只能有一个 `concept_role: "owner"`。在前页只做上下文的元素标记为 `context`，不得提前完整展示由后页拥有的详解卡片。

旧项目没有 `visual_actions` 时，审计会临时以既有 `sync_events` 作为兼容清单并在报告中标记兼容模式；新项目必须使用 `--require-manifest` 建立显式清单。

## 严格语义同步事件

`sync_events` 只记录必须贴合真实口播的语义动作：

```json
{
  "id": "attention-label",
  "scene_id": "attention",
  "label": "注意一下",
  "stage": "semantic",
  "audio_time": 15.25,
  "visual_time": 15.25,
  "audio_end": 15.8
}
```

`stage` 省略时视为 `semantic`，兼容旧项目。误差帧数为 `abs(visual_time - audio_time) * fps`：不超过 `0.5` 帧通过；`(0.5, 1]` 帧警告；超过 `1` 帧失败。

## 可选预入场事件

短句临近转场时，可让容器、轮廓或弱化类别标签先淡入，避免卡片一闪而过；完整语义文字、关键词和高亮仍只能在严格语义事件的真实词位出现。

```json
{
  "prelude_events": [
    {
      "id": "attention-shell",
      "for_event_id": "attention-label",
      "scene_id": "attention",
      "visual_time": 14.7,
      "kind": "container"
    }
  ]
}
```

- `for_event_id` 必须引用同一场景的一条 `semantic` 事件。
- `kind` 仅能是 `container`、`outline` 或 `muted-label`。
- 预入场必须早于目标语义事件，最多领先 `0.75s`；它不参与半帧误差计算，目标语义事件才参与。
- 不得在预入场展示未来口播的完整信息，也不得把预入场当作同步通过证据。

## 修复原则

- 保留已确认的镜头、素材和技术表达；只改目标问题和同类缺陷。
- 音频长时增加信息价值，不增加无意义的装饰或静止。
- 音频短时优先删减非关键视觉节拍，不牺牲概念顺序。
- 不确定的重复、口误或未朗读内容必须标记为待人工确认，不能擅自剪掉。
- 场景边界可随真实语义调整。不要为了保留旧分镜时长，让动作一次性播完后静止等待口播。
