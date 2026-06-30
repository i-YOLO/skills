---
name: mofang-illustrations
description: 为中文知识内容策划、生成、编辑和交付“墨方”风格位图插画。用于用户提供文章、主题、观点、截图或 Markdown，并需要 shot list、正文配图、墨方头像、世界观设定图、墨方 IP 视觉、批量配图，或明确要求真实使用 Image Gen 生图与迭代时。不用于包装印刷、矢量转曲、Illustrator、PDF 生产或 OpsHub 流程。
---

# Mofang Illustrations

## 核心定位

把中文知识内容翻译成“墨方正在搭系统”的原创视觉隐喻，并用内置 `image_gen` 完成真实生成、编辑、评图和位图交付。

墨方是一只章鱼型系统架构师：圆头、圆框眼镜、半眯眼、黑色领结、多条承担实际工作的触手，常操作系统魔方。让墨方始终承担画面的核心动作，不要把它当吉祥物或装饰。

## 先读取参考

每次任务都读取：

- `references/style-dna.md`
- `references/character-ip.md`
- `references/qa-checklist.md`

按任务追加读取：

- 内容选图与 shot list：`references/profile.md`、`references/workflow.md`、`references/composition-patterns.md`
- 编写生图 brief：`references/prompt-template.md`
- 需要起始方向：`references/seed-prompts.md`
- 正式落盘与交付：`references/asset-delivery.md`

不要默认打开全部案例图。只在需要校准线条、留白和色彩时查看 `assets/examples/`，并遵守反复刻规则。

## 三条路线

### 1. 策略模式

当用户只要策略、shot list、brief 或 prompt 时：

1. 提炼核心观点、认知转折和视觉锚点。
2. 短内容输出 1–3 张、常规内容输出 4–8 张 shot list。
3. 为每张图写清放置位置、核心意思、结构类型、墨方动作、保留项、可改项、禁止项、比例和交付形式。
4. 不调用 `image_gen`，不声称已经生成图片。

### 2. 生成模式

当用户要求真实生图时：

1. 先确定单图 brief 或完整 shot list。
2. 将 `assets/avatar/01-mofang-social-avatar.png` 作为角色身份参考图。
3. 仅在世界观设定图任务中追加 `assets/avatar/02-mofang-worldview-ip-sheet.png`。
4. 将任务归类为 `stylized-concept`，使用 `references/prompt-template.md` 组织 prompt。
5. 默认调用内置 `image_gen`；不使用 OpsHub，不读取浏览器 token，不轮询外部任务。
6. 多图任务按 shot list 一图一次调用。不要用一次请求代替多个不同资产，也不要因为用户说“批量”就切换 CLI。
7. 检查每张输出；不合格时只改变一个变量，做一次定向重生或编辑，再重新检查。
8. 预览任务内联展示；正式任务按交付规则落盘并报告绝对路径、最终 prompt 和所用模式。

### 3. 编辑模式

当用户要求修改现有图片时：

1. 明确标注每张输入图的角色：编辑目标、角色参考、风格参考或合成素材。
2. 本地编辑目标尚未出现在对话中时，先用 `view_image` 检查。
3. 列出“只改什么”和“必须保持什么”，并把不变项写进每轮 prompt。
4. 使用内置 `image_gen` 编辑，默认另存版本化文件，不覆盖原图。
5. 对身份、构图、文字和未指定区域逐项复核。

## Image Gen 执行规则

- 正文配图默认 16:9 横版；头像默认 1:1；世界观设定图默认 1:1，除非用户指定。
- 默认生成无文字图片。只有用户明确要求时才加入少量逐字短标签，并专项核对准确性。
- 参考图只锁定角色身份和风格 DNA，不照搬其具体构图、文案或节点布局。
- 内置 `image_gen` 不可用时，说明 CLI fallback 需要 `OPENAI_API_KEY`；只有用户明确同意后才切换。
- 简单透明背景请求先生成纯色色键底图，再使用系统 `imagegen` Skill 的 `remove_chroma_key.py` 去背并验证 alpha。
- 遇到毛发、烟雾、玻璃、液体、半透明或反光主体时，先说明原生透明需要 CLI `gpt-image-1.5`，取得用户确认后再执行。
- 不创建或维护自定义生图 API 脚本。

## 参考图角色

- `assets/avatar/01-mofang-social-avatar.png`：所有真实生成的默认角色身份参考；锁定头型、眼镜、眼神、领结、触手和系统魔方。
- `assets/avatar/02-mofang-worldview-ip-sheet.png`：只用于世界观与完整能力设定图，不用于普通头像。
- `assets/examples/`：只用于校准手绘线条密度、留白、克制色彩和隐喻节奏；除非用户明确要求，否则禁止复刻具体构图。

## 输出口径

- 策略任务：先给 shot list 或 brief，保持短而具体。
- 真实生成：先展示结果；正式交付同时给绝对路径、最终 prompt、参考图角色和 Image Gen 模式。
- 多图任务：逐张列出主题与路径，明确哪些是最终稿、哪些是被淘汰的迭代稿。
- 不把位图描述成矢量稿，不承诺 Illustrator、转曲、印刷或 PDF 生产能力。
