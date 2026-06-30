# Image Gen Prompt 模板

## 正文配图

```text
Use case: stylized-concept
Asset type: Chinese knowledge-content editorial illustration
Primary request: {主题与核心意思}
Input images: Image 1 is the canonical Mofang character identity reference; preserve identity, do not copy its composition
Scene/backdrop: clean warm-white or pale-cool-gray background with generous negative space
Subject: Mofang, an octopus system architect, actively {核心动作}
Style/medium: restrained hand-drawn graphite line illustration, slightly loose system-sketch feeling
Composition/framing: 16:9 landscape; {结构类型与空间关系}; one visual idea only
Lighting/mood: quiet, lucid, thoughtful, long-termist, subtly strange
Color palette: graphite black with sparse functional electric blue and orange; red only for a critical warning
Materials/textures: paper-like linework, no glossy commercial finish
Constraints: preserve round head, round glasses, half-lidded eyes, black bow tie, working tentacles and system cube; Mofang performs the core action; no text unless explicitly requested; original composition; generous whitespace
Avoid: mascot cuteness, childish cartoon, PPT infographic, courseware, dense architecture diagram, purple-blue AI aesthetic, cyber glow, gradients, complex background, watermark, copied example composition
```

## 社媒头像

```text
Use case: stylized-concept
Asset type: social avatar
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
Constraints: preserve {角色身份、构图、背景、比例、未指定区域}; change only {指定修改}; no new text; no extra objects; no watermark
```

## 用户明确要求短标签时

添加：

```text
Text (verbatim): "{逐字文本}"
Constraints: render each requested label exactly once; no other text; keep labels short and legible
```

生成后逐字检查；错误时优先减少标签或单独修正文字，不同时改变构图。
