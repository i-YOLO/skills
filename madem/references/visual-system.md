# 默认视觉系统

默认知识口播使用 `1920×1080`、60fps 的浅色预设。AI、Agent、Codex 和软件工作流题材自动改用 `1080×1920` 的 `madem-ai-tech-dark-v1`；用户明确指定比例或品牌规范时覆盖自动路由。

## 画布与色板

- 背景固定为纯色 `#FAF8F3`；禁止渐变、纹理、噪点和暗角。
- 正文深蓝 `#12315B`；亮蓝 `#2563EB`；强调橙 `#FF6B1A`；成功绿 `#2F9E76`。
- 卡片白 `#FFFCF7`；次级底色 `#F4EFE6`；边框米灰 `#D8CEBE`；弱化文字 `#64748B`；风险红 `#D95D5D`。
- 直接复制 `assets/design-system/visualDefaults.ts` 或读取 `visual-defaults.json`；纯色背景图位于同目录。

## 字幕与安全区

- 字幕：`49px`、白色、字重 700、纯黑 `10px` 描边、`paint-order: stroke fill`，禁止阴影、发光和模糊。
- 所有画幅默认强制单行，允许自动缩小到 `36px`；仍放不下时按真实词位拆成两条连续字幕，禁止换行、裁切或继续缩小。
- 16:9 底边距 `86px`、左右边距 `140px`、最大宽度 `1540px`；9:16 底边距 `86px`、左右边距 `70px`、最大宽度 `940px`。
- 字幕专属区域为 `x=140–1780、y=860–1040`。非字幕内容在 `y=820` 前结束，与字幕区至少保留约 `48px`。
- 使用 `assets/remotion-caption-overlay/CaptionOverlay.tsx`；不要在项目中继续沿用旧的 44px、2px 描边或阴影样式。

## 几何与间距

- 同一横向流程中的卡片、节点以几何中心共线；内容高度不同也不改变中心线。
- 连接线和箭头穿过同一中心线，不从卡片顶部或底部随内容高度漂移。
- 独立卡片、动画、标签、角色和连线至少留出 48px 或等比例安全间距；不得覆盖、压线或穿字。
- 标题左安全线与核心图形的首个外边界对齐。先修锚点和组宽，再改卡片尺寸，最后才调整字号。

## 产品界面

- 解释聊天、文件、搜索、待办、工作流或仪表盘时，优先用 `KnowledgeVisuals.tsx` 的模拟视图展示真实状态变化。
- 可以借鉴真实产品的信息架构与交互习惯，但使用中性名称和中性界面；不得伪造真实截图、Logo 布局或未证实功能。
- 产品图标只用于入口和产品集合提示，默认不显示图标下方小字。统一使用透明 220×220 资产，并按肉眼大小归一，不只按文件边界等宽。
- 所有中文界面文字由 Remotion 绘制；普通卡片仅用于抽象对比、总结和无法界面化的概念。

## 资产路由

- 产品图标：`assets/product-icons/catalog.json`。
- 高清 AI 产品图标：`assets/product-icons/v2/catalog.json`；使用方法见 [product-icon-pipeline.md](product-icon-pipeline.md)。
- YOLO IP：`assets/ip/yolo/catalog.json`。
- YOLO 逐帧动效：`assets/ip/yolo-motion-v1/catalog.json`；Remotion 接入组件为 `assets/remotion-animation-library/YoloMotion.tsx`。
- 动画和模拟界面：`assets/remotion-animation-library`。
- AI 知识封面：`references/cover-style.md` 与 `assets/covers/ai-knowledge-high-density`。
- AI 科技密集动效：`assets/remotion-animation-library/DenseTechMotion.tsx` 与 [dense-motion-system.md](dense-motion-system.md)。

## AI 科技暗色预设

- 画布 `1080×1920`、60fps，背景 `#06090D`，程序化网格 `#25313B`，主强调 `#39FF91`。
- 内容不得超过 `y=1600`；字幕安全区为 `x=70–1010、y=1660–1870`。
- Remotion 使用 PNG 中间帧和原生目标分辨率。`540×960` 只能输出带 `draft` 标识的快速草稿，不得交付。
- 薄线、透明图标边缘、字幕和最终画面必须在编码后的 1080×1920 MP4 上复核。

## YOLO 动效槽位

- 默认显示高度 `320px`，建议 `280–340px`，硬上限 `380px`。
- 角色脚底固定在 `y=820`，只使用 `x=80–460` 的左下槽位或 `x=1460–1840` 的右下槽位。
- 人物、放大镜、卡片等道具保持独立透明层；左右朝向读取独立资产。
- 角色动作不得覆盖标题、卡片、连线或字幕安全区；约 90 秒视频默认使用 4–6 次，每幕最多一个角色动作。
