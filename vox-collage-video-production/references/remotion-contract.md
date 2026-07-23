# Remotion 动画合同

## 模板使用

初始化项目会复制 `assets/remotion-template/` 到 `<project>/remotion/`。在该目录安装依赖后：

```bash
npm install
npm run typecheck
npm run studio
npm run render:preview
npm run render:master
```

将批准的透明素材复制到 `remotion/public/assets/`，将音频复制到 `remotion/public/audio/narration.wav`，并在 `assets.json` 中以 `render_path` 记录相对 public 路径。不得直接引用用户缓存或工具生成目录。

## 分层动画

以静止终画面为起点：先安排主体、载体、辅助物和字幕安全区，再把对象放到画外或遮罩下，反推其入场轨迹。每个独立图层记录 `primary`、`secondary`、`tertiary` 或 `ambient` 动作层级。

- `primary`：承担知识变化，可大幅滑入、揭开、转轴、落下或盖章。
- `secondary`：在主焦点建立后进入，承接因果或对比。
- `tertiary`：仅进行短距离纸艺动作。
- `ambient`：背景、纸纹和浅景深视差，几乎静止。

避免三件以上独立物同时入场；除非同步到达本身有明确含义。定格后留出阅读时间，再开始下一个变化。

## 同步与字幕

使用真实 `Caption[]`，不得按固定时长硬切。核心视觉动作的触发帧相对目标口播词不得超过 ±3 帧；在审核表列出每个触发词、目标帧、实际帧和偏差。

字幕最多两行，使用格式专属安全区。字幕不是场景标题，不应与同时出现的多张解释卡竞争。中文、数字、图表、流程线和标签由代码绘制。

## 审阅证据

每场至少提供：入口、稳定定帧、出口、5–12 秒预览。检查静止状态下的焦点、朝向、共同落点、遮挡和字幕空位；检查播放状态下的分拍入场、触发同步和转场连续性。全片审计后再人工终审。
