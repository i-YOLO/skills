# 视频任务数据结构

所有时间均为秒；所有帧误差都以最终输出 `fps` 计算。不要在没有真实音频时给 `words` 填估算的词级时间。

## `video-job.json`

```json
{
  "schema_version": "1.1",
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
  "scenes": []
}
```

## `timeline.json`

```json
{
  "schema_version": "1.1",
  "fps": 60,
  "audio": null,
  "scenes": [
    {
      "id": "scene-01",
      "start": 0.0,
      "end": 5.0,
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
  "prelude_events": [],
  "sync_events": []
}
```

静音阶段先登记 `visual_actions`：所有语义性标题、卡片、标签、节点、连线、高亮和 CTA 都要有 `id`、`scene_id`、`element_type`、`sync_required` 和概念归属。真实音频到位后，为每个 `sync_required` 动作补 `sync_event_id` 与严格语义同步事件。

`words` 只能由真实 ASR 或经过人工校正的时间轴填充。`sync_events` 用于严格词位验收，结构见 `$sync-explainer-video` 的 `references/sync-schema.md`；`prelude_events` 只记录最多提前 `0.75s` 的容器/轮廓/弱化标签，不替代语义同步事件。

## `qa-report.json`

保留脚本输出的 `status`、`checks`、`issues`、`sync`、`manual_review` 和证据文件路径。不要删除失败记录；修复后新增一轮结果与时间戳。

有口播的发布版还应在 `delivery` 中记录字幕文件与 `caption_report`，以及默认音乐的 `audio_mix_report`、`profile_id`、项目内音乐路径和 SHA-256。静音阶段只保留 `post_sync_defaults`，不得标为已配字幕或已混音。
