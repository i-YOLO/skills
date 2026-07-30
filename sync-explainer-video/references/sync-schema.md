# 声画同步数据结构与修复边界

schema 1.4 向后兼容 1.3，并为高密度动效增加 `motion_density` 和 `visual_actions[].attention_level`。字段与审计规则见 `$madem` 的 `references/dense-motion-system.md`。

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
  "visual_exit_start": 19.2,
  "audio_start": 13.1,
  "audio_end": 23.0,
  "hold": false
}
```

`audio_start` 和 `audio_end` 应围住该场景实际解释的语义，不要仅按整个视频的总时长分配。

## 视觉动作清单

在静音分镜阶段登记所有有意义的标题、卡片、标签、节点、连线、高亮、CTA 和角色动作。收到音频后，动作清单成为同步覆盖率的依据；不要求为纯背景光效、页码等装饰登记。

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
      "visible_from": 15.25,
      "settled_at": 15.6,
      "min_visible_seconds": 1.0,
      "min_settled_seconds": 1.0,
      "concept_id": "word-timed-key-action",
      "concept_role": "owner"
    }
  ]
}
```

- `element_type` 使用 `card`、`label`、`node`、`title`、`highlight`、`cta`、`connection` 或 schema 1.3 新增的 `character-motion`。
- `sync_required: true` 的动作必须有一条语义同步事件；`order` 可选，用于显式检查排比、流程和循环的口播顺序。
- `visible_from` 是元素首次可见时间；完整语义元素不得早于对应 `sync_event.visual_time`。容器预入场应登记为独立的非语义元素和 `prelude_event`。
- `settled_at` 是入场、绘制或展开完全完成的时间；`min_settled_seconds` 默认 `1.0`。每个场景必须满足 `visual_exit_start - settled_at >= min_settled_seconds`。
- 顺序动画的每项可用相同 `sequence_group_id` 和递增 `sequence_index` 登记；组完成时间取最大 `sequence_index` 对应动作的 `settled_at`，不能取第一项出现时间。
- `visible_until` 可覆盖场景结尾；卡片、标签、节点、标题、高亮和 CTA 默认至少需要 `1.0s` 的可见时长，或使用合规预入场。
- 一个 `concept_id` 只能有一个 `concept_role: "owner"`。在前页只做上下文的元素标记为 `context`，不得提前完整展示由后页拥有的详解卡片。
- `attention_level: "high"` 表示主语义入场；其 `visible_from → settled_at` 区间不得与同场景另一个高注意力入场重叠超过 `0.1s`。

## Schema 1.4 密集动效轨道

`motion_density.tracks` 只记录不参与词位误差计算的状态层和环境层：

- `role: "state"`：进度、扫描、失败、修改、重渲等因果状态。
- `role: "ambient"`：低强度波形、呼吸、粒子或窄扫描光。
- 每条轨道包含 `id`、`scene_id`、`start`、`end`、`intensity`；循环环境轨增加 `loop_period_seconds`。
- 环境轨不能替代严格语义事件，也不能用来掩盖整页提前播完。
- 音频拉长后，超过 3 秒的语义空档优先补状态变化；只有没有新状态可表达时才补低强度环境动效。

### Schema 1.3 角色动作

`character-motion` 必须补充：

- `motion_asset_id`：统一 catalog 中的动作 ID，例如 `yolo-verify-source`。
- `motion_variant`：结果分支，例如 `verified` 或 `not-found`。
- `motion_phase`：`idle`、`prepare`、`key-action`、`outcome`、`settled` 之一。
- `facing`：`left` 或 `right`，使用独立生成的对应朝向资产。
- `occupied_rect_1080p`：1080p 占位框，必须完全位于 `x=80–460、y=440–820` 或 `x=1460–1840、y=440–820` 的角色槽位。

同一动作的 `prepare`、`key-action`、`outcome`、`settled` 使用相同 `sequence_group_id` 和递增的 `sequence_index`，每个阶段分别绑定真实口播词位。`outcome` 和 `settled` 的 `min_settled_seconds` 不得小于 `1.0`。角色提前静止出现时，单独登记 `motion_phase: "idle"`、`sync_required: false`；不得把角色静止出现登记成 `prelude_event`。

`motion_asset_id` 必须先从 `$madem/assets/registry.json` 定位 pack，再从 pack catalog 唯一解析 `facing` 和 `motion_variant`。新项目建议在动作对象的 `metadata` 保存 `motion_pack_id`、pack catalog schema 版本、资产状态和项目内 catalog 路径，作为可复现证据；这些元数据不能替代上述必需字段。

默认只选择 `project-proven` 或 `library-approved`。`candidate` 必须在项目中显式采用并保留技术与人工视觉报告。项目渲染读取复制进项目的资产子集，不依赖全局 Skill 路径，也不直接读取知识库中的试做文件。阶段时间使用 catalog 的真实节点和 tick，不按帧数平均切分；不得跳帧、镜像或光流补间来强行贴词位。完整规则见 [character-motion-sync.md](character-motion-sync.md)。

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
- 箭头、标签、答案和下一阶段节点属于未来状态，必须在对应语义发生前完全不可见。SVG 路径进度为零时不得保留 `markerEnd`。
- 循环、返回、继续和完成路径分别维护进度；不得以一个共享进度同时暴露多条路径。
- 角色动作的准备、关键动作、结果、落定分别锚定真实词位；结果状态至少保持 1 秒。角色仅提前静止出现时使用非同步 `idle`，不占用预入场规则。

## 发布字幕与背景音乐边界

- 同步报告永远对照原始口播音频和 `words`；烧录字幕、背景音乐、响度或编码变化都不得改写词级锚点。
- 默认发布字幕的文字来自已确认口播稿，`words` 只提供时间；字幕生成在同步后、BGM 前进行。
- 默认 BGM 在 `$madem` 的最终拼接阶段加入，不登记为 `visual_actions`、`sync_events` 或 `prelude_events`，也不能作为同步通过证据。
