# 转录与文案提取

## 原则

- 逐字稿必须来自真实音频转录。
- 不用标题、简介、章节、字幕摘要或模型猜测冒充逐字稿。
- 摘要和重点提炼必须基于完整逐字稿。
- 转录失败时报告失败，不生成“看起来合理”的文案。

## 音频准备

从完整视频或音频轨抽取 Whisper 用 WAV：

```bash
python3 /Users/shike/.codex/skills/social-video-digest/scripts/extract_audio.py "<input>" "<outdir>/audio.wav"
```

默认参数：`16000 Hz`、`mono`、`pcm_s16le`。

## Whisper

中文内容默认：

```bash
whisper "<outdir>/audio.wav" --model small --language zh --output_format txt --output_dir "<outdir>"
```

英文内容用 `--language en`；语言不明确或中英混合较多时去掉 `--language` 让 Whisper 自动识别。

## 读取和校验

- 读取完整 `audio.txt`，不要只读开头。
- 逐字稿超过 50 个汉字或英文词后，再生成重点提炼。
- 逐字稿过短：只输出逐字稿和“内容过短，未生成提炼”。
- 逐字稿为空：报告失败。

## 纠错口径

- 可以修正常见 ASR 错字，让文案更可读。
- 专有名词无法确认时标记 `[?]`。
- 不确定的句子不要强行补全。
- 如果输出“成片文案”，必须标注它是基于真实逐字稿整理，不是原始逐字稿。

## 清理

临时目录只删除本次 workflow 自己创建的内容。默认保留用户可复核的素材、音频、逐字稿和结果文件。
