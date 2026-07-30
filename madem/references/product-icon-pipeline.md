# 高清透明 AI 产品图标

首版只使用 `assets/product-icons/v2/catalog.json` 中经过用户确认的十个产品。图标只用于产品入口识别，不代表官方背书，也不得拿来伪造产品截图。

## 选择与更新

- 组件按 `assetId` 选择，禁止按数组下标选择。
- SVG 优先；没有确认过的 SVG 时使用 1024×1024 RGBA PNG。
- Gemini 和 Coze 保留 catalog 锁定的原始图形，不重绘、不替换。
- Grok 只允许清理与画布边缘连通的白色/灰色四角；内部白色字形必须保留。
- 默认不联网刷新。品牌更新必须显式执行、更新哈希，并重新人工检查透明、白色和黑色三种背景联系表。

## 构建与验证

```bash
python scripts/prepare_product_icons.py \
  --catalog assets/product-icons/v2/catalog.json

python scripts/render_product_icon_contact_sheet.py \
  --browser <chrome-or-chromium> --update-catalog

python scripts/test_visual_assets.py
```

每个资产必须记录官方域名、来源文件、标准文件、来源 SHA-256、标准文件 SHA-256、透明包围盒和状态。每次更新都要重新生成透明棋盘格、纯黑和纯白三联联系表。新增图标先标为 `candidate`；真实项目和用户确认后升为 `project-proven`。
