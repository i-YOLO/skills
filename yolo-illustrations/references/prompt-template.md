# 生图提示词模板

每张图单独调用 Image Gen。把变量替换为当前内容，不要把多张图拼在一起。

## 共同身份块

将以下内容放入所有新图提示词：

```text
Input images:
- Image 1 is the strict canonical full-body identity reference for YOLO.
- Image 2 is the face, glasses, hair texture, and line-density reference.
- Optional Image 3 is a composition-only reference. Do not copy its object, pose, or layout.

Recurring character required:
YOLO, a 2.5-head chibi young Chinese male with a huge asymmetric fluffy deep-sea-navy hairstyle weighted to viewer-left, a crescent cowlick at upper-left, an outward tuft on viewer-right, oversized rounded-rectangle deep-sea-navy glasses, simple vertical navy eyes, a tiny nose, a slight focused smile, white negative-space face and hands, and one short orange diagonal cheek mark below the viewer-right lens. He wears an electric-blue cropped puffy work jacket with an oversized deep-sea-navy triangular collar, a plain white crew-neck shirt, deep-sea-navy straight trousers, and oversized orange sneakers. Preserve these identity anchors exactly.

Visual DNA:
Pure white background. Loose colored-pencil and wax-crayon texture. Visible grain, slightly imperfect repeated navy outlines, flat waxy fills, and generous white negative space. Use only deep sea navy #17243A, electric blue #2F6BFF, action orange #FF7A1A, and white. No realistic skin color, gradients, shadows, 3D, polished vector art, PPT infographic, formal flowchart, dense UI, logo, watermark, or extra character.
```

## 16:9 正文插图

```text
Generate one standalone 16:9 Chinese article body illustration.

Theme:
{正文配图主题}

Core idea:
{只写一个核心判断或关系}

Structure type:
{流程动作 / 系统局部 / 前后对比 / 角色状态 / 概念隐喻 / 方法分层 / 地图路线 / 小漫画分镜}

Composition:
{YOLO 在哪里、亲自做什么、主物件是什么、动作产生什么结果}

Chinese handwritten labels, exact text:
{0-5 个短标注；无标注时写 none}

Constraints:
YOLO must perform the core conceptual action, not decorate the scene. Use one core action, one or two main objects, at most two motion paths, and at least 35% clean white space. Do not add a title or write the structure type. Invent a fresh physical metaphor for this content; do not copy any calibration example.
```

## 16:9 文章封面

```text
Generate one standalone 16:9 Chinese article cover illustration.

Exact title, reproduce verbatim:
"{标题}"

Optional exact subtitle:
"{副标题或 none}"

Core visual metaphor:
{一个主场景}

Character action:
{YOLO 亲自执行的一个动作}

Composition:
Create a clear title-safe area and place the character scene on the opposite side. Keep the full hair silhouette, glasses, face, and active hands unobstructed. The title is the only dominant text. Do not add category labels, extra slogans, logos, frames, UI panels, or decorative paragraphs.
```

## 4:5 观点卡片

```text
Generate one standalone 4:5 vertical Chinese viewpoint card.

Exact viewpoint, reproduce verbatim:
"{8-18 字核心句}"

Visual action:
{一个手势或一个道具，说明观点而不是重复文字}

Composition:
Set the viewpoint in two or three readable handwritten lines. Use deep sea navy for the main sentence and action orange for at most one emphasized phrase. Place YOLO in the lower or side region, large enough to preserve identity. Use one prop at most and keep at least 25% white space. No subtitle, paragraph, speech bubble, border, logo, or extra label.
```

## 局部编辑

```text
Edit the provided image. Change only {指定变量}.

Required change:
{准确描述要移除、替换或修正的内容}

Preserve exactly:
YOLO's identity, hair silhouette, glasses, cheek mark, outfit, pose, hands, all correct text, palette, line texture, composition, aspect ratio, and image quality.

Do not add any new text, object, color, character, border, logo, or watermark.
```

## 中文纠错

第一次只修错误文字：

```text
Edit only the incorrect Chinese text "{错误文字}" and replace it with the exact text "{正确文字}". Match the existing hand-drawn colored-pencil lettering, size, position, color, and baseline. Preserve every other pixel-level element and do not add new words.
```

若仍不准确，减少标注数量并重新生成整张图，不在同一次返修里改变构图或角色。
