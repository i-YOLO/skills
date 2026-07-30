# AI 科技高密度动效系统

用于 AI 工具、Agent、Codex、软件操作和自动化工作流题材。视觉预设为 `madem-ai-tech-dark-v1`，节奏预设为 `dense-tech-v1`。

## 三层运动

1. **语义层**：标题、步骤、结论、节点和状态变化。严格绑定真实词位，同一时刻只让一个高注意力动作入场。
2. **状态层**：进度、扫描、检查、失败、修改、重渲。用于长句中的因果推进，不得伪造真实产品能力。
3. **环境层**：低强度呼吸、波形、粒子和窄扫描光。只填补视觉空档，不得遮挡字幕或抢夺语义焦点。

密集不等于同时播放。先安排语义动作，再用状态层维持因果变化，最后才添加环境层。

## `dense-tech-v1` 节奏

- 整体语义动作密度建议为每秒 `0.55–0.85` 个。
- 口播持续时，超过 `3.0s` 没有新语义动作，必须有 `state` 或 `ambient` 轨；`hold: true` 除外。
- 环境循环建议为 `1.6–2.5s`，强度必须为 `low`。
- 顺序动画的最终状态至少保持 `1.0s`。
- 超过 `7.0s` 的场景至少包含三个语义或状态节点。
- 最终编码视频的 `visual_qc.static_candidates` 必须为空。

运行：

```bash
python scripts/audit_motion_density.py \
  --timeline <timeline.json> --visual-qc <visual-qc.json> \
  --out <motion-density-report.json>
```

## Schema 1.4

`motion_density` 为可选字段；使用 `dense-tech-v1` 时必须提供：

```json
{
  "schema_version": "1.4",
  "motion_density": {
    "profile_id": "dense-tech-v1",
    "tracks": [
      {
        "id": "quality-scan",
        "scene_id": "scene-10",
        "role": "ambient",
        "start": 40.0,
        "end": 49.0,
        "intensity": "low",
        "loop_period_seconds": 1.67
      },
      {
        "id": "repair-state",
        "scene_id": "scene-10",
        "role": "state",
        "start": 46.5,
        "end": 49.0,
        "intensity": "medium"
      }
    ]
  }
}
```

需要检查主焦点冲突的语义动作增加 `attention_level: "high"`。审计以 `visible_from` 到 `settled_at` 作为入场窗口；两个高注意力入场窗口不得重叠超过 `0.1s`。

## 组件路由

- 多个产品图标聚合、吞噬、吸入、收纳：`IconSwarmCollector`。
- 自动检查、失败、修改、重渲、通过：`QualityInspectionLoop`。
- 证明多种动画能力：`MotionGallery` 与六种 `MicroMotion`。
- 多种动效最终聚合到一个容器：`MotionGatherTransition`。
- 暗色软件窗口和科技网格：`TechGridSceneShell`、`AppWindowFrame`、`NeonTag`。

复制 `DenseTechMotion.tsx`、`ProductIcon.tsx` 和实际使用的图标文件到项目内，不得让成片依赖全局 Skill 路径。
