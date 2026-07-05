# 小红书流程

## 链接要求

优先使用用户复制的完整公开分享链接，例如：

```text
https://www.xiaohongshu.com/explore/<note_id>?xsec_source=app_share&type=video&xsec_token=<token>
```

经验结论：裸 `https://www.xiaohongshu.com/explore/<note_id>` 或 `discovery/item/<note_id>` 可能能识别笔记 ID，但经常拿不到视频格式。不要删除 `xsec_token`。

## 元数据探测

```bash
yt-dlp --dump-single-json --no-download --no-playlist "<完整公开分享链接>"
```

记录标题、正文、标签、作者 ID、时长、分辨率和格式。

## 下载

```bash
yt-dlp -o "<outdir>/source.%(ext)s" "<完整公开分享链接>"
```

下载后用 `scripts/probe_media.py` 校验。

## 失败处理

- 完整分享链接遇到 SSL EOF 或握手失败时，先重试：
  ```bash
  yt-dlp --impersonate chrome -o "<outdir>/source.%(ext)s" "<完整公开分享链接>"
  ```
  这只是公开请求指纹兜底，不导入登录态。
- 裸链接提示 `No video formats found`：要求用户补完整公开分享链接，尤其是 `xsec_token`。
- 短链无法展开或过期：要求用户重新复制分享链接。
- 只有图文没有视频：报告“非视频笔记或无公开视频格式”。
- 不使用登录态、cookies 或非公开接口补齐内容。
