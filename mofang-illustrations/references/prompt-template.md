# Image Gen Prompt 模板

Use `references/style-registry.md` before choosing a template. Keep one image per prompt.

## 手绘系统草图风：正文配图

```text
Use case: stylized-concept
Asset type: Chinese knowledge-content editorial illustration
Style ID: mofang-handdrawn-system-sketch
Primary request: {主题与核心意思}
Input images: Image 1 is the canonical Mofang character identity reference; preserve identity, do not copy its composition
Scene/backdrop: clean warm-white or pale-cool-gray background with generous negative space
Subject: Mofang, an octopus system architect, actively {核心动作}
Style/medium: restrained hand-drawn graphite line illustration, slightly loose system-sketch feeling
Composition/framing: 16:9 landscape; {结构类型与空间关系}; one visual idea only
Lighting/mood: quiet, lucid, thoughtful, long-termist, subtly strange
Color palette: graphite black with sparse functional electric blue and orange; red only for a critical warning
Materials/textures: paper-like linework, no glossy commercial finish
Constraints: preserve round head, round glasses, half-lidded eyes, black bow tie, working tentacles and system cube; Mofang performs the core action; {文字约束}; original composition; generous whitespace
Avoid: mascot cuteness, childish cartoon, PPT infographic, courseware, dense architecture diagram, purple-blue AI aesthetic, cyber glow, gradients, complex background, watermark, copied example composition
```

Use this style for personal IP, creator essays, long-term systems thinking, AI collaboration, and system metaphors. Default `文字约束` is `no text`.

## 3D 材质解释图风：解释图

```text
Use case: stylized-concept
Asset type: Chinese knowledge-content explainer illustration
Style ID: guizang-material-explainer
Primary request: {用普通语言描述概念、流程、机制或图表视觉隐喻}
Scene/backdrop: off-white studio background with generous safe margins
Structure: {cycle / pipeline / hub-and-spoke / before-after / layer-stack / data-first scene / scientific mechanism / text scene}
Chinese labels: {无文字，或逐字列出 3-5 个已确认短标签}. Place each label near the matching object or flow; keep labels horizontal, large, high-contrast, readable, and away from edges.
Style/medium: clean Swiss editorial 3D material illustration, black ink outlines, refined gray surfaces, soft studio light, one vivid accent color
Composition/framing: {16:9 / wide horizontal 1.9:1 / 1:1}; full subject visible; no crop; centered vertically
Lighting/mood: crisp studio light, calm analytical mood
Constraints: no extra words beyond confirmed labels, no unrelated English, no logo, no watermark, no poster frame, no page title, no decorative blobs, no gradient background
Avoid: dense legend, paragraph text inside the image, cramped screenshot layout, wrong data, unsupported historical/scientific facts
```

Use this style for workflows, mechanisms, chart beautification, education, technical concepts, and label-first center illustrations.

## 社媒头像

```text
Use case: stylized-concept
Asset type: social avatar
Style ID: mofang-handdrawn-system-sketch
Primary request: create or refine a highly recognizable Mofang avatar
Input images: Image 1 is the canonical identity reference
Subject: centered Mofang holding or operating one system cube
Style/medium: restrained black hand-drawn line art on a clean light background
Composition/framing: 1:1 square, compact silhouette, safe for circular crop
Constraints: preserve round head, glasses, half-lidded calm expression, black bow tie, multiple working tentacles and system cube; no labels; no extra icons
Avoid: worldview modules, long text, glossy commercial rendering, excessive cuteness, watermark
```

## 世界观设定图

```text
Use case: stylized-concept
Asset type: Mofang worldview character sheet
Style ID: mofang-handdrawn-system-sketch
Primary request: express Mofang's system-thinking capabilities through visual modules
Input images: Image 1 is the canonical avatar identity reference; Image 2 is the worldview reference for capability coverage only, not for text or layout copying
Subject: Mofang centered and actively coordinating a restrained set of capability modules
Style/medium: hand-drawn system sketch with graphite linework and sparse functional color
Composition/framing: 1:1 square, clear hierarchy, generous whitespace
Constraints: preserve character identity; use icons and actions instead of text by default; keep modules sparse and readable; create an original spatial arrangement
Avoid: avatar-only crop, copied reference layout, PPT grid, dense labels, watermark
```

## 编辑模板

```text
Use case: precise-object-edit
Asset type: Mofang illustration edit
Primary request: change only {指定修改}
Input images: Image 1 is the edit target; Image 2 is the canonical Mofang identity reference
Constraints: preserve {角色身份、构图、背景、比例、未指定区域}; change only {指定修改}; no new text unless explicitly requested; no extra objects; no watermark
```

## 短标签候选块

Before generation, propose labels instead of asking the user to fill them from scratch.

```markdown
推荐图内短标签：
- {标签 1}
- {标签 2}
- {标签 3}
- {标签 4}

请选择：直接使用 / 修改后使用 / 不加图内文字 / 放到外层文字
```

Label rules:

- Use Simplified Chinese by default.
- Prefer 3-5 labels.
- Prefer 2-5 Chinese characters per label; 8 characters is the upper limit.
- Use concrete labels such as `目标`, `执行`, `检查`, `迭代`; avoid abstract stage names when concrete object labels work.

## 逐字文字块

Only add this block after the user confirms labels.

```text
Text (verbatim): "{标签 1}", "{标签 2}", "{标签 3}", "{标签 4}"
Text constraints: render each requested label exactly once; no other text; keep labels horizontal, short, legible, and near the matching object or flow.
```

生成后逐字检查。错误时优先减少标签或单独修正文字，不同时改变构图。

## 数据准确性块

Use this block for chart screenshots, tables, metric lists, benchmark results, or any image where values matter.

```text
Required chart accuracy: chart type must be {图表类型}. Category order must be exactly: {类别顺序}. Axis labels and units must be exactly: {坐标轴与单位}. Values must be exactly: {逐项数值}. Error bars or ranges must be exactly: {误差线/范围，若有}.
Do not add extra categories. Do not swap order. Do not invent tick labels or values. Data marks must visually match the listed values.
```

If exact values cannot be read, ask for data or mark the values as approximate in the prompt record. Do not invent data.
