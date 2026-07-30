# 视频任务数据结构

所有时间均为秒；所有帧误差都以最终输出 `fps` 计算。不要在没有真实音频时给 `words` 填估算的词级时间。

## `video-job.json`

```json
{
  "schema_version": "1.4",
  "phase": "silent-production",
  "inputs": {
    "script": "script.md",
    "audio": null,
    "assets": ["assets/logo.png"],
    "source_project": null
  },
  "delivery": {
    "output": "out/final.mp4",
    "width": 1920,
    "height": 1080,
    "fps": 60,
    "codec": "h264",
    "audio_mode": "silent",
    "visual_system": {
      "profile_id": "madem-warm-knowledge-v1",
      "background": "#FAF8F3",
      "caption_safe_region_1080p": {"x_min": 140, "x_max": 1780, "y_min": 860, "y_max": 1040},
      "content_max_y_1080p": 820
    },
    "post_sync_defaults": {
      "captions": {
        "enabled_for_voiceover_publish": true,
        "status": "deferred-until-voiceover",
        "text_source": "approved-script",
        "timing_source": "real-word-timeline"
      },
      "background_music": {
        "enabled_for_voiceover_publish": true,
        "status": "deferred-until-voiceover",
        "profile_id": "madem-default-bgm-v3",
        "override_requires_user_request": true
      }
    }
  },
  "motion_density": null,
  "scenes": []
}
```

## `timeline.json`

```json
{
  "schema_version": "1.4",
  "fps": 60,
  "audio": null,
  "scenes": [
    {
      "id": "scene-01",
      "start": 0.0,
      "end": 5.0,
      "visual_exit_start": 4.5,
      "engine": "remotion",
      "hold": false,
      "narration_active": true,
      "audio_start": null,
      "audio_end": null
    }
  ],
  "keywords": [{"text": "时间轴", "time": 2.4}],
  "transitions": [{"id": "cut-01", "time": 5.0}],
  "words": [],
  "visual_actions": [],
  "motion_density": {
    "profile_id": "dense-tech-v1",
    "tracks": [
      {
        "id": "scene-01-scan",
        "scene_id": "scene-01",
        "role": "ambient",
        "start": 0.0,
        "end": 5.0,
        "intensity": "low",
        "loop_period_seconds": 2.0
      }
    ]
  },
  "prelude_events": [],
  "sync_events": []
}
```

静音阶段先登记 `visual_actions`：所有语义性标题、卡片、标签、节点、连线、高亮、CTA 和角色动作都要有 `id`、`scene_id`、`element_type`、`sync_required`、`settled_at`、`min_settled_seconds` 和概念归属。场景必须登记 `visual_exit_start`，且 `visual_exit_start - settled_at >= min_settled_seconds`。真实音频到位后，为每个 `sync_required` 动作补 `sync_event_id` 与严格语义同步事件。

AI 科技高密度项目使用 schema 1.4 的 `motion_density.profile_id: "dense-tech-v1"`。状态层和环境层登记到 `motion_density.tracks`；需要检查主焦点冲突的语义动作增加 `attention_level: "high"`。旧 schema 1.3 保持兼容，但新密集项目必须提供显式轨道并通过 `audit_motion_density.py`。

`character-motion` 还必须包含 `motion_asset_id`、`motion_variant`、`motion_phase`、`facing` 和 `occupied_rect_1080p`：

```json
{
  "id": "verify-source-result",
  "scene_id": "scene-03",
  "element_type": "character-motion",
  "motion_asset_id": "yolo-verify-source",
  "motion_variant": "verified",
  "motion_phase": "outcome",
  "facing": "right",
  "occupied_rect_1080p": {"x_min": 80, "x_max": 460, "y_min": 440, "y_max": 820},
  "sequence_group_id": "verify-source-sequence",
  "sequence_index": 3,
  "sync_required": true,
  "sync_event_id": "verify-result-word",
  "settled_at": 18.2,
  "min_settled_seconds": 1.0,
  "concept_owner_scene_id": "scene-03"
}
```

动作的准备、关键动作、结果、落定分别登记，沿用同一个 `sequence_group_id` 并通过 `sequence_index` 保持阶段顺序。提前静止出现的角色使用 `motion_phase: "idle"` 和 `sync_required: false`，不登记为 `prelude_event`。

`words` 只能由真实 ASR 或经过人工校正的时间轴填充。`sync_events` 用于严格词位验收，结构见 `$sync-explainer-video` 的 `references/sync-schema.md`；`prelude_events` 只记录最多提前 `0.75s` 的容器/轮廓/弱化标签，不替代语义同步事件。

## `qa-report.json`

保留脚本输出的 `status`、`checks`、`issues`、`sync`、`manual_review` 和证据文件路径。不要删除失败记录；修复后新增一轮结果与时间戳。

有口播的发布版还应在 `delivery` 中记录字幕文件与 `caption_report`，以及默认音乐的 `audio_mix_report`、`profile_id`、项目内音乐路径和 SHA-256。静音阶段只保留 `post_sync_defaults`，不得标为已配字幕或已混音。
