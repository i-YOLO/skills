# Style Registry

Use this reference before writing prompts or calling `image_gen`.

The user-facing style options should describe the look and use case. Do not expose internal names such as "Mofang" or "Guizang" in the option labels. Internal `style_id` values are only for prompts, manifests, and handoff records.

## Registry Fields

Every style profile must define:

- `style_id`
- User-facing style name.
- Suitable use cases.
- Unsuitable use cases.
- Default aspect ratio.
- Text policy.
- Reference-image policy.
- Prompt requirements.
- QA requirements.

New styles should be added here without changing the main workflow.

## Initial Styles

### Hand-drawn System Sketch

- `style_id`: `mofang-handdrawn-system-sketch`
- User-facing name: `手绘系统草图风`
- Suitable for: personal IP visuals, system thinking, AI collaboration, long-termism, creator essays, reflective articles, knowledge-work metaphors, and recurring editorial illustrations.
- Unsuitable for: exact chart redraws, dense process diagrams, scientific diagrams where the mechanism must be explicit, and images whose main purpose is label-first explanation.
- Default aspect ratio: 16:9 for editorial illustrations, 1:1 for avatars and worldview sheets.
- Text policy: default no in-image text. For explainers, workflow diagrams, or mechanism images, propose 3-5 short Chinese label candidates and ask before generation.
- Reference-image policy: use `assets/avatar/01-mofang-social-avatar.png` for identity in normal generation. Use `assets/avatar/02-mofang-worldview-ip-sheet.png` only for worldview sheets.
- Prompt requirements: Mofang must perform the core action. Use clean light backgrounds, graphite black linework, sparse functional blue/orange/red, generous whitespace, and one visual idea.
- QA requirements: identity preservation, active tentacles, non-mascot tone, original composition, no PPT/courseware feel, no copied example composition, and text correctness when labels are used.

### 3D Material Explainer

- `style_id`: `guizang-material-explainer`
- User-facing name: `3D 材质解释图风`
- Suitable for: process diagrams, mechanism diagrams, chart beautification, educational explanations, technical concepts, data-first editorial images, and center illustrations that need clear labels or arrows.
- Unsuitable for: Mofang IP avatar work, worldview sheets, highly personal creator identity visuals, and tasks where hand-drawn brand consistency matters more than explanation.
- Default aspect ratio: 16:9 for slide/doc visuals, wide horizontal 1.9:1 for social-card image wells, 1:1 only when required by the final layout.
- Text policy: labels are allowed when they clarify the diagram. Propose 3-5 short Chinese labels before generation; keep each label 2-5 Chinese characters when possible and no more than 8 characters.
- Reference-image policy: do not use Mofang avatar references by default. Gather factual or visual references for niche entities, scientific objects, historical/cultural context, brands, model families, maps, or places.
- Prompt requirements: clean Swiss editorial 3D material illustration, off-white background, black ink outlines, refined gray surfaces, one accent color, safe margins, readable labels, and no decorative blobs or gradient background.
- QA requirements: label spelling and placement, no cropped labels or objects, accurate chart data, correct reference cues, no accidental logos/watermarks, and readable composition at the intended display size.

## Agent Choice Rules

- If the user chooses a style, use it.
- If the user chooses "让 Agent 判断", decide from the content and explain the reason before asking the next preflight question.
- Prefer `mofang-handdrawn-system-sketch` for personal IP, essays, long-term systems thinking, and visually branded article illustrations.
- Prefer `guizang-material-explainer` for explicit processes, mechanisms, charts, educational diagrams, and label-first center visuals.
- When a task needs both, split deliverables: use the 3D material style for exact explanation assets and the hand-drawn style for editorial/IP memory assets.
