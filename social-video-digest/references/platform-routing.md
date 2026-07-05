# 平台路由

## URL 识别

- 抖音：`douyin.com/video/<aweme_id>`、包含 `modal_id=<aweme_id>` 的抖音链接。
- B站：`bilibili.com/video/<BV>`、`b23.tv` 短链。
- 小红书：`xiaohongshu.com/explore/<note_id>`、`xiaohongshu.com/discovery/item/<note_id>`、`xhslink.com` 分享短链。
- 其他：交给 `yt-dlp` 探测。

## 标准化

- 抖音公开视频优先标准化为：
  ```text
  https://www.douyin.com/video/<aweme_id>
  ```
- B站公开视频优先标准化为：
  ```text
  https://www.bilibili.com/video/<BV>
  ```
- 小红书优先保留用户给出的完整公开分享链接，尤其保留 `xsec_token`、`xsec_source` 和 `type=video`。

## 处理顺序

1. 提取 URL 和本地文件路径。
2. 每条链接创建独立输出目录：`outputs/social-video-digest/<platform>/<id>/`。
3. 按平台读取对应流程文件。
4. 先做元数据/可下载性探测，再下载。抖音优先在隔离浏览器中标准化到详情页、稳定播放器、至少轮询两次、枚举所有 `video` 选择主播放器，再读取并分类 `video.currentSrc`；若出现登录弹窗先关闭；`http(s)` 直接下载，`blob:` / 空值先短等并尝试 `pageAssets.list()` 恢复视频轨和音频轨，默认模式下 `yt-dlp` 只作为最后回退。
5. 下载后必须用 `scripts/probe_media.py` 校验，不以扩展名或文件大小判断成功。

## 降级策略

- B站：`yt-dlp` 失败时报告错误；不自动使用登录 cookies。
- 小红书：裸 `explore/<note_id>` 失败时，请用户补完整公开分享链接。
- 抖音：先在隔离浏览器中稳定播放器、至少轮询两次、枚举所有 `video` 选择主播放器，再读取并分类 `video.currentSrc` 作为首选下载源；若出现登录弹窗先关闭；`currentSrc` 为空、`blob:` 持续不变、不可下载或校验失败时，先尝试 `pageAssets.list()` 恢复视频轨和音频轨，再在默认模式下回退 `yt-dlp`，用户明确要求先不用 `yt-dlp` 时直接失败。
- 其他平台：`yt-dlp` 不支持或失败时，只报告失败原因和人工补齐建议。
