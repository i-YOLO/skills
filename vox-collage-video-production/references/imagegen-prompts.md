# VOX 纸艺拼贴 ImageGen 提示词

默认通过内置 `$imagegen` 生成。每个 `asset_id` 单独调用，记录最终提示词到 `design/prompts/<asset-id>.md`；默认一张，不为“多给选择”重复生成。

## 统一风格前缀

```text
Use case: stylized-concept
Asset type: Remotion-ready editorial paper-collage asset
Style/medium: original editorial paper-collage, warm off-white paper texture,
deep cobalt blue as the main color, vermilion red accent, black-and-white halftone
printing for people and objects, mixed cut-paper and torn-paper edges, restrained
paper fiber, subtle print-registration error, a consistent soft shadow cast toward
the lower right, flat collage rather than a 3D render
Constraints: clean hierarchy, generous negative space, fully visible subject,
no Chinese text, no numbers, no letters, no logo, no watermark, no UI, no chart labels
```

根据项目格式补充构图约束：横版说明左右留白，竖版说明上下节奏和字幕底部安全区，方图说明中心主体与四边安全区。生成图不承担精确文字。

## 核心主体：透明素材

```text
[统一风格前缀]
Primary request: one independent [人物 / 机器 / 书 / 卷轴 / 照片组]
Subject: [正面 / 朝左侧面 / 朝右侧面] 的完整单一主体
Scene/backdrop: perfectly flat solid #ff00ff chroma-key background for local removal
Composition/framing: generous padding around the complete subject; no crop
Constraints: intended for independent Remotion animation; no extra prop, no second subject,
no cast shadow, no floor, no reflection
Avoid: text, numbers, logos, watermark, repeated limbs, duplicate object
```

## 手部与交互动作

```text
[统一风格前缀]
Primary request: one [左手 / 右手] entering from [左侧 / 右侧 / 上方],
performing exactly one action: [拿起纸片 / 推动卡片 / 盖章 / 拉开卷轴 / 操作按钮]
Scene/backdrop: perfectly flat solid #ff00ff chroma-key background for local removal
Composition/framing: complete wrist and hand, natural fingers, clear gesture, generous padding
Constraints: one hand only; no arm beyond what the action needs; no body, desk, prop duplicate,
no shadow or reflection
Avoid: extra hand, fused fingers, missing fingers, text, numbers, watermark
```

## 载体、机器、容器

```text
[统一风格前缀]
Primary request: one [编辑台 / 纸张轨道 / 打印机 / 档案抽屉 / 相框]
Composition/framing: [正视 / 三分之二视角] with a clearly empty area for later paper,
photo, or hand interaction in Remotion
Scene/backdrop: perfectly flat solid #ff00ff chroma-key background for local removal
Constraints: simple, complete, isolated object; no person, no complex setting, no screen UI
Avoid: readable text, numbers, logos, watermark, duplicate machine
```

## 辅助素材包

```text
[统一风格前缀]
Primary request: a spaced set of separate helper paper assets: [朱红撕纸色带 / 钴蓝纸条 /
胶带 / 图钉 / 胶片条 / 波形纸条]
Scene/backdrop: perfectly flat solid #ff00ff chroma-key background for local removal
Composition/framing: every item complete, isolated, with visible gaps for later cutting
Constraints: consistent lower-right shadow; no words or symbols; no main character or scene
```

## 档案画面

```text
[统一风格前缀]
Primary request: one complete [历史照片 / 手稿档案 / 科学观察图 / 抽象资料拼贴]
Style/medium: monochrome halftone print with restrained cobalt and vermilion paper accents
Composition/framing: a rectangular in-frame asset for a paper frame or book page
Constraints: torn or cut-paper edge is allowed; no readable writing, numbers, logos, watermark
```

## 前景遮挡和转场纸片

```text
[统一风格前缀]
Primary request: one large [钴蓝 / 朱红 / 米白] torn-paper foreground mask
Composition/framing: irregular paper edge, enough blank surface to enter from [左 / 右 / 上 / 下]
and reveal the next scene
Scene/backdrop: perfectly flat solid #ff00ff chroma-key background for local removal
Constraints: no text, pattern, person, or extra object
```

## 透明处理与复检

对于简单不透明主体，先走绿幕/洋红幕，再使用 ImageGen 的本地抠图工具。检查：透明通道、四角透明、边缘毛边、键色溢出、完整主体、朝向、肢体和重复对象。头发、烟雾、玻璃、液体和反光复杂物件优先改为整块画面或遮罩；需要原生透明 CLI 时必须先征得用户确认。
