# social-video-digest

统一处理公开视频素材：下载视频、提取音频、生成真实 ASR 逐字稿，并基于逐字稿做重点提炼。适用于个人学习、对标拆解和自媒体脚本研究。

> 说明：Codex 触发 skill 时主要读取 `SKILL.md`。本 README 是给人看的安装和使用说明。

## 依赖安装

### macOS 推荐安装

```bash
brew install ffmpeg
brew install --cask google-chrome
uv tool install --python 3.12 --force 'yt-dlp[default,curl-cffi]'
uv tool install --python 3.12 --force openai-whisper
uv tool update-shell
```

如果不用 `uv`，也可以用 Python 环境安装：

```bash
python3 -m pip install -U 'yt-dlp[default,curl-cffi]' openai-whisper
```

### 必需命令

- `yt-dlp`：B站、小红书和其他公开平台下载。
- `ffmpeg` / `ffprobe`：抽音频、合并音视频、校验媒体轨道。
- `whisper`：真实音频 ASR 转录。
- Google Chrome：抖音公开视频在 `yt-dlp` 失败时，用隔离 Chrome 公开播放路线。

### 环境检查

```bash
yt-dlp --version
ffmpeg -version
ffprobe -version
whisper --help
'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --version
```

如果 `yt-dlp` 或 `whisper` 装在 `~/.local/bin` 但命令不可用，确认 PATH 包含：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## 配置约定

- 默认输出目录：当前工作区下的 `outputs/social-video-digest/<platform>/<id>/`。
- 默认 Whisper 模型：`small`。
- 默认中文转录参数：`--language zh`。
- 不配置、不导入、不复用登录 cookies。
- 不使用扫码、验证码、手机号、密码或私有接口。
- 不自动写入 LifeOS；需要沉淀时，在提示中明确说“写入/保存到项目/沉淀到 Obsidian”。

## 平台链接格式

### 抖音

优先使用公开视频详情页：

```text
https://www.douyin.com/video/<aweme_id>
```

说明：

- `yt-dlp` 直抓抖音可能失败。
- 若公开视频页能未登录自然播放，skill 会走隔离 Chrome 公开播放路线，保存自然加载的音视频分轨并合并。
- 不使用现有浏览器登录态。

### B站

优先使用公开视频路径：

```text
https://www.bilibili.com/video/<BV>
```

说明：

- 优先用 `yt-dlp` 下载。
- 不使用 cookies 获取会员、付费或非公开格式。

### 小红书

优先使用完整公开分享链接：

```text
https://www.xiaohongshu.com/explore/<note_id>?xsec_source=app_share&type=video&xsec_token=<token>
```

说明：

- 不要删除 `xsec_token`。
- 裸 `explore/<note_id>` 可能只能识别笔记 ID，但拿不到视频格式。
- 遇到 SSL EOF 时，可让 skill 用 `--impersonate chrome` 重试公开请求。

## 如何在 Codex 中使用

### 只下载视频

```text
使用 $social-video-digest 下载这个公开视频：
https://www.bilibili.com/video/BVxxxx
```

### 只提取音频

```text
使用 $social-video-digest 从这个本地视频提取音频：
/path/to/source.mp4
```

### 只提取逐字稿/文案

```text
使用 $social-video-digest 提取这个视频的真实逐字稿：
https://www.xiaohongshu.com/explore/...?...xsec_token=...
```

### 全流程

```text
使用 $social-video-digest 全流程处理这个公开视频：下载、校验、提取音频、Whisper 转录，并输出重点提炼：
https://www.douyin.com/video/<aweme_id>
```

## 直接使用脚本

### 校验媒体轨道

```bash
/Users/shike/.codex/skills/social-video-digest/scripts/probe_media.py /path/to/source.mp4
```

输出会包含：

- `has_video`
- `has_audio`
- 编码
- 分辨率
- 时长
- 文件大小

### 提取 Whisper 音频

```bash
/Users/shike/.codex/skills/social-video-digest/scripts/extract_audio.py /path/to/source.mp4 /path/to/audio.wav --force
```

输出音频参数：

- `16000 Hz`
- `mono`
- `pcm_s16le`

### 合并音视频分轨

```bash
/Users/shike/.codex/skills/social-video-digest/scripts/merge_av.py /path/to/video-only.mp4 /path/to/audio-source.m4a /path/to/source.mp4 --force
```

合并后脚本会再次校验，只有同时包含视频轨和音频轨才算完整视频。

## 输出内容

常见输出文件：

- `source.mp4`：完整视频。
- `video-only.mp4`：仅视频轨。
- `audio-source.m4a`：原始音频轨。
- `audio.wav`：Whisper 用音频。
- `transcript.txt`：完整逐字稿。
- `metadata.json`：公开元数据。
- `result.md`：用户明确要求保存时的整理结果。

## 边界

- 只处理公开可访问内容。
- 只做个人学习、对标拆解、文案结构分析。
- 不搬运、不洗稿、不重新分发平台内容。
- 逐字稿必须来自真实音频 ASR；标题、简介、章节和模型猜测不能冒充逐字稿。
- 失败时直接报告失败原因，不编造摘要。
