# Scene JSON Schema

Use this schema as the intermediate representation between PNG understanding and SVG generation.

AI vision should output this JSON, not final SVG. Python scripts validate this structure and render PPT-safe SVG deterministically.

## Top Level

```json
{
  "version": "0.1",
  "canvas": {"preset": "ppt169", "width": 1280, "height": 720},
  "source": {"image": "../images/source.png", "width": 1280, "height": 720},
  "assessment": {
    "suitability_score": 4,
    "recommended_mode": "hybrid",
    "notes": "Rebuild text, panel, radar chart; bake classroom and character art."
  },
  "layers": [],
  "animation_plan": [],
  "elements": []
}
```

## Element Fields

Common fields:

```json
{
  "id": "title-main",
  "type": "group",
  "class": "Editable",
  "animatable": true,
  "children": []
}
```

Supported element types:

- `group`
- `rect`
- `circle`
- `ellipse`
- `line`
- `path`
- `polygon`
- `polyline`
- `text`
- `image`

## Text Element

```json
{
  "id": "title-main-text",
  "type": "text",
  "x": 320,
  "y": 150,
  "text": "我是班级小英雄",
  "font_size": 64,
  "font_family": "Microsoft YaHei",
  "font_weight": "700",
  "fill": "#FFF1C7",
  "stroke": "#3A1E0E",
  "stroke_width": 6,
  "anchor": "middle"
}
```

## Image Element

```json
{
  "id": "background-image",
  "type": "image",
  "href": "../images/slide_bg.png",
  "x": 0,
  "y": 0,
  "width": 1280,
  "height": 720,
  "preserve_aspect_ratio": "xMidYMid slice"
}
```

## Grouping Rules

- Put animation targets as top-level `group` elements in `elements`.
- Keep non-animated background in `id: "background"` or `id: "bg-..."`.
- Prefer stable semantic ids over visual ids: `radar-node-responsibility`, not `circle-7`.
- Children may be any supported element type.

## Confidence

Optional confidence fields help review:

```json
{
  "confidence": 0.82,
  "needs_review": false,
  "review_reason": ""
}
```

Use `needs_review: true` for uncertain OCR, unclear chart data, or low-confidence object boundaries.

## AI Prompt Contract

When prompting an AI model, require:

- JSON only, no Markdown.
- First element is a baked full-canvas `background` group referencing the source image.
- Important text appears again as editable `text` elements.
- Future animation targets are top-level `group` elements.
- Complex art remains baked unless it can be cleanly approximated with simple SVG-safe shapes.
