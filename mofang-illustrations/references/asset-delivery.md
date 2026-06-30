# 位图交付规则

## 保存位置

1. 用户指定目录时，保存到该目录。
2. 正式项目未指定目录时，保存到当前项目的 `outputs/mofang-illustrations/<内容主题>/`。
3. 仅预览或头脑风暴时，可内联展示并保留 Image Gen 默认生成位置。

## 正式目录

```text
<内容主题>/
├── brief/
│   ├── shot-list.md
│   ├── prompts.md
│   └── run-manifest.md
├── iterations/
└── final/
```

- `brief/`：保存最终 shot list、实际使用的 prompts 与运行清单。
- `iterations/`：保存需要保留的定向迭代稿；被明确淘汰且无复用价值的版本可不保留。
- `final/`：只保存最终选定的 PNG 或 WebP。

## 运行清单

多图正式任务在首次生成前创建 `brief/run-manifest.md`，至少记录：

```markdown
# Run Manifest

- strategy: balanced
- initial_concurrency: 3
- retry_concurrency: 2
- started_at: 2026-01-01T10:00:00+08:00
- finished_at:
- wall_time_seconds:

| asset_id | topic | batch | status | iterations | prompt | final_path | error |
|---|---|---:|---|---:|---|---|---|
| 01-signal-filter | 信号过滤 | 1 | planned | 0 | prompts.md#01-signal-filter |  |  |
```

状态只使用：`planned`、`running`、`pass`、`rework`、`rejected`、`failed`。每次批次结束后按 `asset_id` 更新，不依赖调用完成顺序推断资产身份。

任务结束时填写 `finished_at` 和 `wall_time_seconds`。需要验证并发收益时，使用相同 shot list 分别运行 `strict` 与 `balanced`，比较总墙钟时间和 QA 通过率；不要把单张耗时相加替代并发任务的真实墙钟时间。

## 命名

- 使用清晰主题名，例如 `signal-filter.png`、`agent-orchestration.png`。
- 已存在文件不可覆盖；使用 `-v2`、`-round2` 或 `-edited`。
- 多图使用稳定序号，例如 `01-signal-filter.png`。

## 交付口径

- 报告每张最终图的绝对路径。
- 同时报告最终 prompt、参考图角色、Image Gen 模式和并发策略。
- 对失败资产报告 `asset_id` 和简短错误，不因单张失败隐藏其他成功结果。
- 明确结果是位图，不描述为 SVG、矢量稿、转曲稿或印刷文件。
