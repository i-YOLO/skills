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
│   └── prompts.md
├── iterations/
└── final/
```

- `brief/`：保存最终 shot list 与实际使用的 prompts。
- `iterations/`：保存需要保留的定向迭代稿；被明确淘汰且无复用价值的版本可不保留。
- `final/`：只保存最终选定的 PNG 或 WebP。

## 命名

- 使用清晰主题名，例如 `signal-filter.png`、`agent-orchestration.png`。
- 已存在文件不可覆盖；使用 `-v2`、`-round2` 或 `-edited`。
- 多图使用稳定序号，例如 `01-signal-filter.png`。

## 交付口径

- 报告每张最终图的绝对路径。
- 同时报告最终 prompt、参考图角色和执行模式。
- 明确结果是位图，不描述为 SVG、矢量稿、转曲稿或印刷文件。
