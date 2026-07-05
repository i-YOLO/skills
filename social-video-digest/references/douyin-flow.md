# 抖音流程

## 标准入口

只从公开视频详情页开始：

```text
https://www.douyin.com/video/<aweme_id>
```

如果用户提供的是主页 modal、收藏页、搜索页或带 `modal_id` 的链接，先提取 `aweme_id` 并标准化为详情页。

## 优先尝试

先走隔离 Chrome 公开播放路线，读取 `video.currentSrc` 作为首选下载源：

1. 创建临时 browser profile，不使用用户现有 Chrome profile。
2. 用有界面 Chrome 打开标准详情页；headless 可能停在“视频数据加载中”。
3. 检查页面是否显示“登录”按钮且没有当前用户头像、账号菜单、私信、通知等登录态信号。
4. 等视频自然播放，确认 `video` 元素有真实时长、分辨率和 `readyState`。
5. 读取 `video.currentSrc`，把它记录到 `metadata.json` 的 `videoSrc` 字段，并作为首选下载 URL。
6. 直接下载该 URL，保存为 `source.mp4`；用 `scripts/probe_media.py` 校验。
7. 如果 `source.mp4` 只有单轨、`currentSrc` 为空、不可下载，或下载后 `probe_media.py` 失败，再回退到 `yt-dlp` 探测和下载。
8. 如果 `yt-dlp` 也失败，或页面无法自然播放，停止。

## 回退下载

先探测，再下载：

```bash
yt-dlp --dump-single-json --no-download --no-playlist "https://www.douyin.com/video/<aweme_id>"
yt-dlp --merge-output-format mp4 -o "<outdir>/source.%(ext)s" "https://www.douyin.com/video/<aweme_id>"
```

如果 `yt-dlp` 输出分轨，再用 `scripts/merge_av.py` 合成 `source.mp4` 后重新校验。

## 成功标准

- 页面未登录且自然播放。
- 优先使用 `video.currentSrc` 成功下载。
- 最终 `source.mp4` 可被 `ffprobe` 识别。
- 如用户要求完整视频，`source.mp4` 同时包含视频轨和音频轨。
- 输出公开视频链接、保存目录、文件名、轨道校验和限制说明。

## 失败处理

- 页面无法自然播放：停止并记录“公开播放不可用”。
- 只拿到视频轨：如果用户只需要画面素材，可以交付视频轨；如果用户要真实逐字稿，报告缺少音频，不生成 ASR。
- 只拿到音频轨：可用于转录，但报告缺少视频轨。
- 任何登录、验证码、扫码、手机号输入或页面阻断：停止。
