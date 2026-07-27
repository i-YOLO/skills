# 口播发布版：字幕与默认背景音乐

仅在真实口播完成转录、动作同步和画面审核后执行本流程。静音动画与未同步预览不得添加字幕或背景音乐。

## 默认顺序

1. 从已确认口播稿与 `timeline.json.words` 生成字幕；识别结果只提供时间，不作为观众可见文案。
2. 将 `captions.json` 接入 Remotion 的 `CaptionOverlay.tsx`，或将 `captions.ass` 烧录到非 Remotion 视频；输出带原始口播音轨的字幕版视频。
3. 使用 `extract_review_frames.py --captions <captions.json>` 抽取每秒帧及每条字幕的起始/中间/结束帧，人工检查遮挡风险。字幕默认底部居中、49px 白字、纯黑 10px 描边、无阴影和不透明底板；关键图形位于底部时，先调整画面，不能临时下移字幕安全区。
4. 仅对已验收字幕版运行 `mix_default_bgm.py`。脚本会把默认音乐复制到项目 `public/audio/`，以复制视频流方式输出最终发布版。
5. 以原始口播音频运行同步验收；背景音乐不参与词级对齐，也不能作为动作锚点证据。

## 默认音乐配置

配置文件：`assets/audio/default-bgm-profile.json`。

- `madem-default-bgm-v3`：`Instrumental Minimal` / `The_Mountain`。
- 基础音量 `0.238`（约 `−12.5 dB`），人声侧链避让，片头 `1.2s` 淡入、片尾 `3s` 淡出、循环点 `1s` 等功率交叉淡化。
- 输出为 H.264 原视频流 + AAC 48kHz 单声道 160k 音频。默认音乐不足时自动循环。
- 音乐为用户提供的本地可复用资产；不要将其描述为已核验的公开授权素材。

## 命令

```bash
python scripts/build_captions.py \
  --script <approved-script.md> --timeline <timeline.json> --out <out/captions> --fps <fps>

# 将 assets/remotion-caption-overlay/CaptionOverlay.tsx 复制到目标 Remotion 项目，
# 使用上一步生成的 captions.json 后渲染字幕版视频。

python scripts/mix_default_bgm.py \
  --video <captioned-voiceover.mp4> --project <project-dir> \
  --out <final.mp4> --report <audio-mix-report.json>
```

传入自定义音乐前，必须先获得用户明确的替换授权，并同时使用 `--music <path> --allow-custom-music`；否则保持默认配置。
