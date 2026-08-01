# welcome-wave 右朝向母带返修

- 状态：`source-repaired`
- 日期：2026-07-31
- 范围：仅 `right-a/b/c` 的 chroma、RGBA、提示词与本报告
- 未变更：左朝向母带、全部生产帧、预览与 catalog

## 修复内容

- 重建 A/B/C 连续姿势链：A 抬手，B 完成第一次腕部轻摆并开始第二次，C 完成第二次后自然回落。
- B、C 的前两姿势分别复现上一段最后两姿势；B 的第 8 姿势保持举手，避免提前回落。
- 三段逐姿势重新配准为统一人物可见高度和固定脚底基线；头身比、人物尺度和相机尺度不再随动作递减。
- 所有母带统一为 `2048×768`；每个姿势按目标可见高度 `488px`、脚底基线 `y=639` 配准，水平中心固定在 8 个等宽槽位。
- 背景校正为纯 `#ff00ff`。RGBA 使用显式 `#ff00ff` 键色、soft matte、透明阈值 12、完全不透明阈值 220；未启用 despill。

## 验证

| 母带 | 可见高度比 | 脚底基线范围 | 顶部范围 | 四角 chroma | 四角 alpha |
|---|---:|---:|---:|---|---|
| right-a | 1.002053 | 0px | 1px | `#ff00ff` | 0 |
| right-b | 1.004115 | 1px | 1px | `#ff00ff` | 0 |
| right-c | 1.002053 | 0px | 1px | `#ff00ff` | 0 |

人物高度稳定在 `486–488px`，三段之间没有原先的持续缩小。橙色鞋面、白鞋带与连续白鞋底在全部姿势中保留，未发现重复肢体或残影。

## SHA-256

- `right-a-chroma.png`：`cc6b5390f53aedadd7f3561518c6f16df942dca43828a32fd33e11f47fdadd27`
- `right-a-rgba.png`：`01bc30b728b5b95569ecb6aee42ec8226e513ae7ff18e283f70b7eac0dc31524`
- `right-b-chroma.png`：`e54d849c0a0dd349548e8d1bdf0b45521a458d6c8b185519c55fc485a093b001`
- `right-b-rgba.png`：`bcf0471c76e4a4fe890bebec1147c988b4f5a97e74cd608181730f0cf36c25e4`
- `right-c-chroma.png`：`bcdd6699563df070b217bfe834fff1ee4889d0cb08b6cce9ae830259d290f7b8`
- `right-c-rgba.png`：`da21589f5da1e57a945414f34d93b46dc1265baad1420d382da0961a56dbb990`
