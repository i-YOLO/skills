# B站流程

## 标准入口

优先使用公开视频路径：

```text
https://www.bilibili.com/video/<BV>
```

短链或带追踪参数的链接可先解析或清理为标准路径。

## 元数据探测

```bash
yt-dlp --dump-single-json --no-download --no-playlist "https://www.bilibili.com/video/<BV>"
```

记录标题、作者、时长、发布时间、简介和可用格式。

## 下载

优先下载公开视频可用的最高普通清晰度和音频：

```bash
yt-dlp --merge-output-format mp4 -o "<outdir>/source.%(ext)s" "https://www.bilibili.com/video/<BV>"
```

如果需要指定格式，优先选同时可公开获取的视频格式和音频格式。不要使用登录 cookies 获取会员、付费或非公开格式。

## 校验

下载后运行：

```bash
python3 /Users/shike/.codex/skills/social-video-digest/scripts/probe_media.py "<outdir>/source.mp4"
```

成功标准：

- `has_video: true`
- `has_audio: true`
- 时长与元数据大体一致

## 失败处理

- HTTP 错误、地区限制、内容删除或工具不支持：报告原始错误。
- 只有音频或只有视频：按实际轨道交付，并说明不能标记为完整视频。
- 不使用 cookies 或登录态补齐更高格式。
