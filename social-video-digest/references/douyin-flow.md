# 抖音流程

## 标准入口

只从公开视频详情页开始：

```text
https://www.douyin.com/video/<aweme_id>
```

如果用户提供的是主页 modal、收藏页、搜索页或带 `modal_id` 的链接，先提取 `aweme_id` 并标准化为详情页。

## 优先尝试

先走隔离 Chrome 公开播放路线，读取并分类主播放器的 `video.currentSrc` 作为首选下载源：

1. 创建临时 browser profile，不使用用户现有 Chrome profile。
2. 用有界面 Chrome 打开标准详情页；headless 可能停在“视频数据加载中”。
3. 检查页面是否显示“登录”按钮且没有当前用户头像、账号菜单、私信、通知等登录态信号；如果弹出登录弹窗，先关闭弹窗再继续。
4. 等视频自然播放，至少采样两次，枚举所有 `video`；优先选择正在播放、`currentTime` 在前进、`readyState=4`、`paused=false`、`duration>0` 的主播放器，必要时再比较分辨率。
5. 读取主播放器的 `currentSrc`，把它记录到 `metadata.json` 的 `videoSrc` 字段，并额外记录 `videoSrcType`、`videoPlayerIndex`、`currentTimeAtCapture`、`downloadMethod`。
6. 分类 `currentSrc`：`http(s)` 直接下载，`blob:` 视为暂态不直接下载，空值继续等待；对应的 `downloadMethod` 建议写成 `currentSrc-http-download`。
7. 若读到 `http(s)`，直接下载该 URL，保存为 `source.mp4`；下载请求沿用页面 `Referer` 和浏览器 UA；用 `scripts/probe_media.py` 校验。
8. 若初始为 `blob:` 或空值，继续短时间轮询直到切换为 `http(s)`、超时，或页面公开资产清单里出现可下载媒体 URL。
9. 如果 `source.mp4` 只有单轨、`currentSrc` 持续为 `blob:` 或空值、不可下载，或下载后 `probe_media.py` 失败，启用 `pageAssets.list()` 兜底：先找出播放器真实加载的媒体资源，再分别下载视频轨和音频轨，最后合并成完整视频；这一路的 `downloadMethod` 建议写成 `pageAssets-list-fetch-merge`；仍失败再回退到 `yt-dlp` 探测和下载。
10. 如果 `yt-dlp` 也失败，或页面无法自然播放，停止。

## `pageAssets` 兜底

当 `video.currentSrc` 只给出 `blob:`、空值，或直链下载不可用时，使用浏览器侧资源清单做恢复：

1. 用浏览器里的 `pageAssets.list()` 找到播放器真实加载的媒体资源。
2. 优先匹配视频轨和音频轨资源，例如：
   - `media-video-hvc1`
   - `media-audio-und-mp4a`
3. 用页面上下文的 `fetch` 或等价下载方式，把视频轨保存为 `video-only.mp4`，把音频轨保存为 `audio-source.m4a`。
4. 用 `scripts/merge_av.py` 无损合成 `source.mp4`。
5. 用 `scripts/probe_media.py` 再做一次轨道校验。
6. 在 `metadata.json` 里把兜底来源写清楚，至少记录 `pageAssetsVideoSrc`、`pageAssetsAudioSrc`、`mergeMethod` 和 `downloadMethod`。

## 回退下载

先探测，再下载：

```bash
yt-dlp --dump-single-json --no-download --no-playlist "https://www.douyin.com/video/<aweme_id>"
yt-dlp --merge-output-format mp4 -o "<outdir>/source.%(ext)s" "https://www.douyin.com/video/<aweme_id>"
```

如果 `yt-dlp` 输出分轨，再用 `scripts/merge_av.py` 合成 `source.mp4` 后重新校验。

## 成功标准

- 页面未登录且自然播放。
- 若弹出登录弹窗，已先关闭再继续。
- 主播放器被正确识别，而不是第一个隐藏或预加载的 `video`。
- 优先使用 `video.currentSrc` 成功下载。
- 发生回退时，先尝试 `pageAssets.list()` 恢复媒体 URL，再回退 `yt-dlp`。
- `videoSrcType` 正确区分为 `http(s)` / `blob` / `empty`。
- 最终 `source.mp4` 可被 `ffprobe` 识别。
- 如用户要求完整视频，`source.mp4` 同时包含视频轨和音频轨。
- `metadata.json` 记录的下载来源与最终文件一致。
- 输出公开视频链接、保存目录、文件名、轨道校验和限制说明。

## 失败处理

- 页面无法自然播放：停止并记录“公开播放不可用”。
- 登录弹窗无法关闭且阻断播放：停止并记录“登录弹窗阻断公开播放”。
- `currentSrc` 持续为 `blob:` 或空值且用户要求 Chrome-only：停止并记录“公开播放不可下载”。
- 只拿到视频轨：如果用户只需要画面素材，可以交付视频轨；如果用户要真实逐字稿，报告缺少音频，不生成 ASR。
- 只拿到音频轨：可用于转录，但报告缺少视频轨。
- 任何登录、验证码、扫码、手机号输入或页面阻断：停止。
