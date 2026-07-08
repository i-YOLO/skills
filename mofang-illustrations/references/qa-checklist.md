# QA Checklist

Run this before delivering final images. Reject attractive images when they fail the user's actual content need.

## Universal

- The selected style matches the user's choice or the Agent's stated reason.
- The image answers the content need, not merely the production method.
- The whole subject fits; no important object, label, icon, axis, or data mark is cropped.
- Background is clean, light, and not visually noisy.
- One image explains one core action, structure, state, mechanism, or data point.
- No watermark, unrelated logo, fake UI chrome, or accidental extra characters.
- The image is readable at the intended display size.

## 手绘系统草图风

- Mofang has round head, round glasses, half-lidded eyes, black bow tie, working tentacles, and system cube when required.
- Mofang performs the core action rather than standing beside it.
- Graphite black hand-drawn linework is the visual skeleton; color is sparse and functional.
- The mood is calm, lucid, long-termist, and system-oriented.
- The image does not look like a PPT infographic, courseware page, dense architecture diagram, childish mascot, or commercial flat illustration.
- The composition does not copy examples: no reused telescope crowd layout, seesaw cube, ring network, six-grid agents, full reflect loop, cloud-to-framework layout, or chaos-to-order stage chart unless the user explicitly requests it.

## 3D 材质解释图风

- The image uses clean Swiss editorial 3D material style: off-white background, black ink outlines, refined gray surfaces, soft studio lighting, and one accent color.
- The visual structure matches the chosen mode: cycle, pipeline, hub-and-spoke, before/after, layer stack, data-first scene, scientific mechanism, or text scene.
- Labels, arrows, objects, and flows point to the correct relationships.
- The image does not become a decorative poster; the explanation remains legible.
- No dense legend, paragraph text, decorative blobs, gradient background, or cramped screenshot layout.

## Text

- If the user chose no in-image text, the image contains no labels, headings, fake UI text, or accidental English.
- If labels were confirmed, every label is present exactly once and spelled exactly as confirmed.
- Labels are short, horizontal, readable, high-contrast, and placed near the matching object or flow.
- No extra words beyond confirmed labels unless the prompt explicitly allowed them.
- If labels are wrong, garbled, missing, duplicated, or clipped, regenerate or repair; do not deliver as final.

## Charts And Data

- Chart type matches the source data.
- Category order is correct.
- Axis labels, units, tick labels, and ranges are correct when specified.
- Every value label is exact when exact data was provided.
- Data marks visually match the numbers.
- Error bars or uncertainty ranges appear when requested.
- Scene elements do not block chart reading.
- If exact values cannot be read, the output records uncertainty or asks for data; it must not invent values.

## Reference Facts

- For niche, scientific, historical, cultural, brand, model, map, place, or apparatus topics, reference cues are accurate enough for the intended audience.
- Brand/model/entity icons are stylized cues, not pasted flat logos, unless the user explicitly asks for exact logos.
- Historical, cultural, scientific, or biological details do not imply unsupported certainty.
- Scientific or educational diagrams do not mislead on direction, scale, sequence, or part labels.

## Single-variable Iteration

- Too ordinary: make the core physical action more specific.
- Too complex: remove nodes, labels, or props until one idea remains.
- Too cute: strengthen calm, half-lidded, system architect, not mascot, not childish.
- Too PPT: remove titles, neat grids, explanatory boxes, and excessive arrows; use a scene or material explainer instead.
- Too close to old examples: keep the core meaning, change the main object, action, or spatial relationship.
- Text wrong: only repair text or reduce labels; do not also redesign the composition.
- Data wrong: repair chart data first; do not accept an attractive but inaccurate chart.

## Delivery Judgment

For hand-drawn system sketch style, the reader should first see Mofang actively building or operating a system and understand the core structure in one second.

For 3D material explainer style, the reader should first understand the concept, process, mechanism, or data relationship; style is secondary to clarity and accuracy.
