# deny-shake 母带检查

status: `b-source-repaired`

## 本次返修范围

- 仅替换 `source/right-b-chroma.png`、`source/right-b-rgba.png`、`source/left-b-chroma.png`、`source/left-b-rgba.png`。
- A 母带、生产拆帧、catalog 和现有预览未修改。
- B 的前两姿势直接沿用对应 A 的最后两姿势，消除 A/B 边界“换头”。
- 后续姿势按“回中 → 过中 → 克制的反向极值 → 回中落定”重新排序和注册。

## 自动检查

| 母带 | 尺寸 | 姿势数 | 纯色边界 | 透明四角 | 隐藏 RGB | 高度比 | 鞋底纵向范围 | RGBA SHA-256 |
|---|---:|---:|---|---|---:|---:|---:|---|
| right-b | 2048×768 | 8 | `#ff00ff` 通过 | 通过 | 0 | 1.0040 | 1px | `397db71cbd52d82fc166fbea314b6d0f94ebef7aef69c0ad60a76d56f6f867fc` |
| left-b | 2048×768 | 8 | `#ff00ff` 通过 | 通过 | 0 | 1.0038 | 0px | `97fa2734fdee8a05ffe9160520ecb0335844baaddef8f7897aced320e899c51f` |

RGBA 转换固定使用显式 `#ff00ff`、soft matte、透明阈值 8、不透明阈值 96、edge feather 0.35；未启用 auto-key、spill cleanup 或 despill。

## 人工母带目检

- 左右 B 均为恰好 8 个彼此分离的完整全身姿势，无道具、文字、阴影、分栏、残影或裁切。
- 前两格与 A 尾部使用同一图像内容，人物比例、发型、眼镜透视、五官和鞋底锚点连续。
- 第 3–5 格逐步回到中位；第 6–7 格形成可辨认但克制的反向侧转；第 8 格回中落定。
- 橙色鞋面、白色鞋带、白色鞋底、裤脚和躯干注册稳定。
- 右 B 的反向极值比左 B 更明确；左右都已避免旧版 `F07 → F08` 的单帧侧向到正面跳切。

## 结论

B 母带源修复通过，可进入重新拆帧和 60fps 预览。现有 production keyframes 与 previews 仍对应旧 B，不得用来代表本次修复后的最终动画质量。
