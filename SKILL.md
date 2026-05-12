---
name: pngtosvgtoppt
description: Convert or assess PNG slide images for reconstruction as layered, PPT-safe SVG scenes and editable PowerPoint decks. Use when Codex needs to judge whether PNG/JPG slide screenshots, AI-generated slide images, visual mockups, information graphics, or classroom/game-style pages can become editable and animation-ready PPT; plan element decomposition; create scene JSON; generate structured SVG; validate/finalize SVG; or export editable PPTX with the bundled local converter.
---

# PNG To SVG To PPT

Turn flat PNG slide images into editable, animation-ready presentation scenes. The skill favors practical reconstruction: rebuild high-value text, panels, lines, charts, buttons, and animation candidates as SVG/PPT objects; keep complex backgrounds, characters, photos, and heavy effects as image layers when needed.

This skill is self-contained for SVG validation, SVG finalization, and PPTX export. It embeds the mature SVG-to-PPT pipeline under `scripts/`, adapted from `ppt-master`; do not require the user to switch to or invoke the `ppt-master` skill for these steps.

## Operating Rule

If the user asks only for judgment, suitability, or planning, stop after analysis and do not create conversion artifacts.

If the user asks to convert, generate these outputs in order:

1. Suitability judgment
2. Layer and animation plan
3. Scene JSON, drafted by AI vision when keys are configured or by Codex/manual planning otherwise
4. PPT-safe SVG in `svg_output/`
5. Quality check
6. Local post-processing and PPTX export

## Decision Workflow

1. Inspect the PNG visually and identify the reconstruction goal: exact visual fidelity, editability, animation readiness, or a balanced result.
2. Classify each region as `Editable`, `Animatable`, `Baked`, or `Hybrid`. See `references/reconstruction-policy.md`.
3. Create an animation layer plan before SVG generation. Any future animation target must become an independent top-level `<g id="...">`.
4. Create or update scene JSON using `references/scene-schema.md`. If the user wants AI decomposition, read `references/ai-vision-config.md` and run `scripts/ai_vision_to_scene.py` or `pngtosvgtoppt_pipeline.py ai-scene`.
5. Generate PPT-safe SVG. Use only SVG features listed in `references/svg-ppt-constraints.md`.
6. For PPT export, place SVGs in a project folder `svg_output/`, then run this skill's local quality/post-processing/export scripts.

## Suitability Guide

Prefer conversion when the image contains readable text, panels, diagrams, charts, buttons, icons, lines, simple shapes, or clear foreground objects.

Avoid full structural conversion when the image is mostly photographic, painterly, texture-heavy, or defined by pixel-level effects. Use a baked background plus editable overlays instead.

For AI-generated classroom/game visuals, default to a hybrid plan:

- Baked: classroom background, soft focus, stars/particles when numerous, complex character art, detailed envelope wings, glow halos.
- Editable: titles, body text, CTA text, panels, radar chart, labels, nodes, connectors, buttons.
- Animatable: title groups, envelope, light burst, radar chart, each key node, check mark, character, CTA button, mission panel, star trails.

## Required Grouping

Every top-level semantic object must use a stable group id:

```xml
<g id="title-main">...</g>
<g id="radar-chart">...</g>
<g id="radar-node-responsibility">...</g>
<g id="hero-envelope">...</g>
<g id="cta-button">...</g>
```

Use `background` or `bg-*` ids for non-animated page chrome. The bundled SVG-to-PPTX converter treats top-level `<g id="...">` groups as animation anchors.

## Scripts

Create a starter scene file:

```bash
python3 scripts/png_scene_scaffold.py input.png -o scene.json --canvas ppt169
```

Render a scene file to SVG:

```bash
python3 scripts/scene_to_svg.py scene.json -o slide_01.svg
```

These scripts do not perform AI vision by themselves. They provide deterministic scaffolding and rendering around AI- or human-authored scene JSON.

Draft scene JSON with a configured AI vision model:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py ai-scene input.png --project projects/demo --slide 1 --canvas ppt169
```

Configuration is read from `.env`, the skill directory `.env`, or `~/.pngtosvgtoppt/.env`. Use `.env.example` as the template.

Fully automatic one-image conversion:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py auto input.png --project projects/demo --slide 1 --canvas ppt169
```

Use `auto` whenever the user asks to convert and has not explicitly requested a manual review gate. It runs AI scene decomposition, SVG rendering, quality check, finalization, and PPTX export in sequence.

Run the local end-to-end project pipeline:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py scaffold input.png --project projects/demo --slide 1
python3 scripts/pngtosvgtoppt_pipeline.py ai-scene input.png --project projects/demo --slide 1
python3 scripts/pngtosvgtoppt_pipeline.py render projects/demo/scenes/slide_01.scene.json --project projects/demo
python3 scripts/pngtosvgtoppt_pipeline.py check projects/demo
python3 scripts/pngtosvgtoppt_pipeline.py finalize projects/demo
python3 scripts/pngtosvgtoppt_pipeline.py export projects/demo
```

Shortcut after scene JSON is complete:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py build projects/demo
```

`build` runs `check`, `finalize`, and `export` in order. Use only after the SVGs already exist in `svg_output/`.

## Bundled PPT Pipeline

The skill includes these local mature pipeline components:

- `scripts/svg_quality_checker.py` checks SVG compatibility before export.
- `scripts/finalize_svg.py` writes `svg_final/` and embeds/corrects images, text, icons, and rounded rectangles.
- `scripts/svg_to_pptx.py` exports editable native PPTX plus a preview PPTX.
- `scripts/ai_vision_to_scene.py` calls a configured vision model and writes scene JSON.
- `scripts/scene_validate.py` validates and normalizes scene JSON before rendering.
- `scripts/svg_finalize/` and `scripts/svg_to_pptx/` hold the implementation modules.

The local icon directory is intentionally empty by default to keep the skill lightweight. Prefer direct SVG shapes for reconstructed PNG scenes. If `<use data-icon="...">` placeholders are needed, copy the required icon libraries into `templates/icons/` before running finalization.

## Quality Gates

Before exporting to PPTX:

- Confirm all intended animation targets are separate top-level groups.
- Confirm important text is SVG `<text>`, not baked into the background.
- Confirm complex effects that cannot be reliably edited are intentionally baked.
- Run local `scripts/svg_quality_checker.py` against `svg_output/`.
- Only then run local `scripts/finalize_svg.py` and `scripts/svg_to_pptx.py`.
