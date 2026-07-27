---
name: madem
description: 制作、修复和验收程序化口播动画视频。用于把文案、分镜、图片、视频、Logo 或已有 Manim/Remotion 项目制作成静音动画、预览或最终成片；覆盖镜头设计、引擎路由、Remotion/Manim/FFmpeg 组装、逐页质检、局部修复与 H.264 交付。当用户提到“madem”“口播视频动画”“静音动画”“制作科普/教学/产品演示视频”或要修复已有动画成片时使用。
---

# MADEM：口播动画制作

先做可审核的静音动画，再接收最终口播进行同步。把它当作程序化动画导演与制作流水线；不要把它描述成真人电影生成模型。

## 输入与交付

接受以下任意组合：文案、逐字稿、分镜或动画注释、图片/视频/Logo、已有 Manim 或 Remotion 项目、口播音频，以及目标比例和帧率。

默认交付为 `1920×1080`、`60fps`、H.264 MP4。支持 16:9、9:16、1:1、4:3，24/25/30/50/60fps，静音、有声、音乐、字幕和多音轨。

有真实口播的发布成片默认烧录字幕并使用 `madem-default-bgm-v3` 背景音乐；只有用户明确要求静音、无字幕或替换音乐时才关闭或覆盖。静音动画、预览版和未完成同步的项目不得添加字幕或 BGM。

默认画布使用纯色浅暖白 `#FAF8F3`，不得添加渐变、纹理、噪点或暗角。字幕默认 `49px` 白字、纯黑 `10px` 描边、无阴影，底边距 `86px`、左右边距 `140px`、最大宽度 `1540px`、最多两行。完整色板、安全区和布局常量见 [references/visual-system.md](references/visual-system.md)。

在目标项目目录创建并持续更新以下文件：

- `video-job.json`：输入、输出、分镜和制作阶段。
- `timeline.json`：场景、转场、视觉动作清单、预入场和后续音频时间轴。
- `qa-report.json`：技术检查、视觉审核和同步状态。

使用 `scripts/init_video_job.py` 初始化；完整字段见 [references/job-schema.md](references/job-schema.md)。

## 开工闸门

1. 运行 `scripts/doctor.py --project <project-dir> --model large-v3`。检查 Node/Remotion、Python/Manim、FFmpeg/ffprobe、Faster-Whisper、浏览器、字体、模型缓存、项目路径和锁文件。
2. 仅当用户明确授权安装时，运行 `scripts/bootstrap_runtime.sh --install`。它使用隔离 Python 3.11 环境安装 Faster-Whisper 和 Manim；不要在未获授权时安装任何软件。
3. 使用 `scripts/media_probe.py` 检查所有输入视频和音频。素材、字体、路径或锁文件异常时，先报告并修复阻塞项。

## 制作流程

### 1. 先完成静音动画

分析文案和素材，先输出分镜、视觉锚点、场景时长和静音预览。没有口播音频时，只能称为“静音动画”或“预览版”，绝不能声称完成声画同步。

按画面内容路由并允许混用：

| 内容 | 工具 |
| --- | --- |
| 公式、向量、矩阵、技术结构变化、原理推导 | Manim |
| 卡片、文字层级、UI、进度条、时间线、转场 | Remotion |
| Manim、图片和视频的组合 | Remotion |
| 裁切、拼接、转码、抽帧、九宫格 | FFmpeg |

每个场景只表达一个主概念。把读不清的中文、标题和字幕放入 Remotion 绘制，不要把它们烘焙进 AI 图片。

涉及聊天、软件、文件、搜索、待办、任务执行或仪表盘时，优先制作中性模拟产品界面，让画面呈现真实操作状态和因果变化；不要默认退化为标题加普通卡片。可以借鉴真实产品的信息架构和交互习惯，但不得伪造产品截图、虚构能力或冒充真实界面。产品图标只作为入口提示，界面主体保持中性品牌。

识别口播中的排比句式（并列名词、连续动词、重复句式、`A / B / C` 或 `A → B → C`）。将每个并列项拆为独立视觉元素，按口播语序依次入场、点亮或展开；排比句式默认是节奏动效，不把整句作为静态文本同时铺开。收到真实音频后，将这些入场点锚定到对应词语或停顿。

在渲染前建立 `visual_actions`：登记标题、卡片、标签、节点、连线、高亮和 CTA 的场景、元素类型、概念归属、是否需要同步和最短展示时长。一个需要详细解释的概念只指定一个“拥有”场景；前页只可给中性上下文，不得抢先展示后页的完整详解卡片。完整字段和预入场规则见 `$sync-explainer-video` 的 `references/sync-schema.md`。

### 资产优先与版式契约

先复用、后新建。运行 `scripts/plan_animation_reuse.py --script <script.md> --out <pattern-plan.json>`，再阅读 [references/animation-pattern-library.md](references/animation-pattern-library.md)；根据**语义结构**确认候选，不能只按关键词自动套模板。流程、对比、循环、分层、时间轴、飞轮和排比标签优先使用 `assets/remotion-animation-library/PatternLibrary.tsx`；模拟界面、五层系统、产品入口、Agent 分支和权限门优先使用 `KnowledgeVisuals.tsx`。复制所需组件到目标项目，不让成片依赖全局 Skill 路径。

复用品牌、IP、背景或封面前，读取对应 `assets/**/catalog.json`。产品图标只使用 `assets/product-icons` 中透明、归一化版本；YOLO 只使用 `assets/ip/yolo/poses` 中最终透明姿势。AI 知识类封面读取 [references/cover-style.md](references/cover-style.md)，默认分别构图并交付 4:3 与 3:4。

只有没有资产能正确表达关系时才设计新动画。新动画至少经过一次真实项目、逐秒/事件帧验收和用户确认后，才能抽成可传入文案、色板与节点数据的组件并加入资产库。

带标题、正文和核心图形的页面，先确定几何关系，再调整字号：

- 标题左边安全线是流程、时间线、卡片组和循环图的首个图形**外边界**起点；“视觉居中”只指标题下方剩余区域的垂直安排，不水平居中整组图形。
- 不要盲用 `margin-top: auto` 把图形压到页面底部。双行标题或长正文页优先上移图形组；在 `1920×1080` 下正文与核心图形至少留 `48px`，其他尺寸按比例换算。
- 先修正锚点、间距和组宽度，再调卡片尺寸，最后才压缩字号；不得用缩小文字掩盖布局问题。
- 在设计首幕前先声明固定字幕安全区，并在所有场景使用同一坐标；任何非字幕文字、卡片、角色、箭头、连线和动画都不得进入该区域。字幕区不是最后叠加时才临时腾出的空间。
- 同组横向卡片或节点以**视觉中心点共线**为默认约束；内容高度不同也不能让卡片中心线或流程连接线产生肉眼可见的上下偏移。
- 语义上彼此独立的卡片、动画、标签和连线必须保持清晰间距，不得通过覆盖、穿插或压线制造层级。必须交叉的关系线需避开文字，并让连接关系可辨认。
- 顺序元素、循环或分支全部完成后，最终完整状态必须至少停留 `1.0s` 再开始退场。每个场景登记 `visual_exit_start`，每个视觉动作登记 `settled_at` 和 `min_settled_seconds`；必须满足 `visual_exit_start - settled_at >= min_settled_seconds`。
- 箭头、答案、标签和下一阶段节点在对应语义发生前必须完全不可见。SVG 路径进度为零时不得保留 `markerEnd`；分支、返回和继续路径分别维护独立进度。

### 2. 边生成边审核

每完成一个分镜，先渲染该分镜并抽取场景前、中、后帧；发现问题直接局部修改后重检，不要等全片渲染完成再返工。

处理用户截图标注时，以截图中的场景编号、时间码和被标注图形为修复目标；文字说明与截图编号冲突时，先说明并以截图标识定位，不改相邻场景。

静音全片完成后，运行：

```bash
python scripts/extract_review_frames.py --video <silent.mp4> --timeline <timeline.json> --out <review-dir>
python scripts/visual_qc.py --video <silent.mp4> --timeline <timeline.json> --out <visual-qc.json>
```

抽帧规则：

- 全片每秒抽 1 帧作为基础巡检；帧内存在正常弹入、弹出或转场是允许的。
- 对每个场景额外抽前、中、后帧；对关键词、语义动作、预入场、场景结尾和转场额外抽前/当时/后帧。
- 对每个动作额外抽“落定、稳定阅读、退场前”帧；对 `visual_exit_start` 抽前/当时/后帧。顺序动画以最后一项完成为落定时间。
- 查看生成的帧图并检查空间关系和技术表达；脚本只能筛出静止和技术异常，不能替代对文字、重叠和语义的视觉判断。
- 每次局部版式修复，先检查受影响场景的前、中、后帧与相邻转场前、中、后帧；确认后重渲整片，并基于最终编码 MP4 重新抽帧，不能只看 Remotion 静帧。

必须修复文字重叠、越界或不可读；箭头/连线压字；高亮后文字看不清；不合理布局；元素闪退或单帧闪烁；异常硬切；图片/视频模糊；播放卡顿；技术示意与文案逻辑不一致。

解释文字、结论和下一步提示只能在其依据、步骤或提问已经出现后入场。审核事件帧时同时检查因果顺序，不能只检查最终画面是否完整。

没有在分镜标注 `hold: true` 的情况下，连续 3 个每秒样本几乎无视觉变化且口播仍在继续，视为“疑似长静止”，必须修改。

### 3. 同步最终口播

收到最终音频后，调用 `$sync-explainer-video`。它生成真实逐词时间轴、比较文案与实际朗读，并输出每个场景的同步方案和动作审计。

按单个场景处理时长差：

- 差值在静音场景时长的 `±20%` 内，可以微调停留、转场和动作节奏。
- 差值超过 `±20%`，或调速后看起来生硬时，音频较长则增加有讲解价值的素材、卡片或镜头；音频较短则压缩或移除非关键画面。
- 不得用明显慢放、长时间空转或无意义静止硬拖时长。短句接近转场时，可以让容器、轮廓或弱化标签提前最多 `0.75s` 淡入；完整语义文字与高亮仍严格锚定真实词位。

### 4. 输出发布版字幕与默认 BGM

同步与画面审核通过后，阅读 [references/publishing-delivery.md](references/publishing-delivery.md)。使用 `build_captions.py` 以已确认口播稿生成 SRT、ASS、Remotion JSON 和字幕报告；Faster-Whisper 的 `timeline.words` 只提供真实时间，不能把识别错字作为字幕正文。

在 Remotion 项目复制 `assets/remotion-caption-overlay/CaptionOverlay.tsx` 并使用字幕 JSON；非 Remotion 项目使用 ASS 烧录。默认字幕为底部居中、`49px` 白字、纯黑 `10px` 描边、无阴影和黑底面板，最多两行。使用 `extract_review_frames.py --captions <captions.json>` 检查每条字幕的起始、中间和结束帧是否遮挡画面，再以带原始口播音频的字幕版调用 `mix_default_bgm.py`。它会将默认音乐复制到项目内、在人声期间自动避让，并复制视频流而非重编码画面。

默认 BGM 配置为用户提供的 `Instrumental Minimal`，基础音量 `0.238`（约 `−12.5 dB`）、1.2 秒淡入、3 秒淡出、1 秒循环交叉淡化。背景音乐不参与词级同步；替换音乐需要用户明确授权。

### 5. 修复已有项目或成片

先识别已确认的场景和问题范围，仅改指定部分；然后扫描全片是否存在同类缺陷。修复后重新抽取受影响场景帧、相邻转场帧和整片每秒帧。

## 最终验收

运行：

```bash
python scripts/validate_delivery.py \
  --video <final.mp4> --timeline <timeline.json> --audio <voiceover.wav> \
  --visual-qc <visual-qc.json> --sync-report <sync-report.json> \
  --caption-report <captions-report.json> --audio-mix-report <audio-mix-report.json> \
  --reference-video <captioned-voiceover.mp4> \
  --manual-review pass --out <qa-report.json>
```

只有同时满足以下条件才标记可交付：可完整解码、规格正确、每秒帧和事件帧已人工视觉复核、无未豁免长静止、无必须修复的视觉缺陷，并且 `$sync-explainer-video` 的严格词位、动作覆盖、预入场、展示时长与概念所有权审计均通过。有口播的默认发布版还必须通过字幕报告、BGM 混音报告和字幕版/最终版视频流一致性检查。

阅读 [references/qa-protocol.md](references/qa-protocol.md) 后执行验收。不要因为成功导出 MP4 就声称完成交付。
