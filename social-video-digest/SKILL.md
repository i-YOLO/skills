---
name: social-video-digest
description: Download and process public social-media videos for personal learning, competitor analysis, and script research. Use when the user asks to download, grab, save, inspect, extract audio from, transcribe, summarize, or get copy/transcripts from public Douyin, Bilibili, Xiaohongshu, YouTube, or yt-dlp-supported video/audio links; also use for all-in-one video download, audio extraction, Whisper transcription, and key-point digest workflows.
---

# 社媒视频下载与文案提取

把公开视频或本地视频处理成可复核素材：视频文件、音频文件、真实 ASR 逐字稿和基于逐字稿的重点提炼。默认只输出到对话和本地工作目录，不写入 LifeOS；只有用户明确要求“写入/沉淀/保存到项目”时才写回 Obsidian。

## 必读顺序

1. 每次先读 `references/safety-boundaries.md` 和 `references/platform-routing.md`。
2. 按链接平台再读对应文件：
   - 抖音：`references/douyin-flow.md`
   - B站：`references/bilibili-flow.md`
   - 小红书：`references/xiaohongshu-flow.md`
3. 需要逐字稿、文案、摘要或音频处理时，读 `references/transcript-workflow.md`。
4. 输出前读 `references/output-templates.md`，使用匹配模板。

## 任务路由

- 用户说“下载、抓视频、保存视频”：只下载视频并用 `scripts/probe_media.py` 校验轨道；抖音优先走 `video.currentSrc`。
- 用户说“提取音频”：从已下载视频或用户提供的本地视频中抽音频，使用 `scripts/extract_audio.py`。
- 用户说“文案、逐字稿、转录、提取口播”：获取音频后用 Whisper 转录；不得用标题、简介或常识替代真实逐字稿。
- 用户说“总结、重点、拆解”：必须先有真实逐字稿，再基于逐字稿提炼；无法转录时只报告失败和可补齐项。
- 用户说“全流程、下载并提取文案”：执行元数据识别、下载、轨道校验、音频抽取、Whisper 转录和重点提炼。

## 默认目录

每条链接使用独立目录：

```bash
outputs/social-video-digest/<platform>/<id>/
```

常用文件名：

- `source.mp4`：完整视频，必须尽量包含音视频双轨。
- `video-only.mp4`：仅视频轨。
- `audio-source.m4a`：原始音频轨。
- `audio.wav`：Whisper 用 `16k mono wav`。
- `transcript.txt`：完整逐字稿。
- `metadata.json`：公开元数据或工具输出。
- `result.md`：用户要求保存时的整理结果。

## 工具检查

开始下载或转录前按需检查：

```bash
yt-dlp --version
ffmpeg -version
ffprobe -version
whisper --help
```

缺少依赖时先报告，不自动安装，除非用户明确要求安装。

## 平台优先级

- B站：优先标准公开路径 `https://www.bilibili.com/video/<BV>`，使用 `yt-dlp` 下载和校验。
- 小红书：优先完整公开分享链接；`xsec_token` 缺失时，裸 `explore/<note_id>` 可能拿不到视频格式。
- 抖音：优先标准公开路径 `https://www.douyin.com/video/<aweme_id>`；先在隔离 Chrome 中读取 `video.currentSrc` 作为首选下载源，`yt-dlp` 仅作为回退。
- 其他平台：先用 `yt-dlp --dump-single-json --no-download --no-playlist` 探测，失败则报告原因。

## 脚本

- `scripts/probe_media.py <file>`：输出 JSON，判断视频轨、音频轨、编码、分辨率、时长和大小。
- `scripts/extract_audio.py <input> <output.wav>`：抽取 Whisper 用音频。
- `scripts/merge_av.py <video> <audio> <output.mp4>`：无重编码合并音视频并校验双轨。

脚本失败时，先报告命令、退出码和 stderr 摘要；不要伪造成功文件。

## 核心原则

- 只处理公开可访问内容，只做个人学习、对标拆解、文案结构分析。
- 不使用登录 cookies、验证码、扫码、私有接口、完整评论抓取或粉丝抓取。
- 不搬运、不洗稿、不重新分发平台内容。
- 多链接逐条处理；一条失败不影响后续链接。
- 摘要必须来自真实转录内容；无法确认的专有名词标记 `[?]`。
- 输出必须说明采集边界、保存路径、校验结果、失败原因和人工补齐建议。
