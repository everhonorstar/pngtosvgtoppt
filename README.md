# PNG to SVG to PPT Codex Skill

[中文说明](README.zh-CN.md)

`pngtosvgtoppt` is a Codex skill for rebuilding flat PNG/JPG slide images as layered, PPT-safe SVG scenes and editable PowerPoint decks. It is designed for hybrid reconstruction: keep complex backgrounds or artwork as image layers, and rebuild high-value text, panels, shapes, charts, labels, and animation targets as editable SVG/PPT objects.

## What It Does

- Assesses whether a slide image is worth reconstructing.
- Plans baked, editable, hybrid, and animatable layers.
- Drafts scene JSON with an optional AI vision model.
- Renders scene JSON into PPT-safe SVG.
- Checks and finalizes SVG for PowerPoint compatibility.
- Exports editable PPTX files with grouped animation anchors.

## Install as a Codex Skill

Clone or copy this repository into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/everhonorstar/pngtosvgtoppt.git ~/.codex/skills/pngtosvgtoppt
```

Install Python dependencies:

```bash
cd ~/.codex/skills/pngtosvgtoppt
python3 -m pip install -r requirements.txt
```

Restart Codex so the skill metadata in `SKILL.md` is discovered.

## Configure AI Vision

AI vision is optional. Manual scene scaffolding, SVG rendering, checking, finalization, and PPTX export all run locally.

To enable AI scene decomposition, copy the example env file and fill in your provider values:

```bash
cp .env.example .env
```

Set both the API key and a vision-capable model name before running `ai-scene` or `auto`.

The skill looks for `.env` in this order:

1. Current working directory
2. This skill directory
3. `~/.pngtosvgtoppt/.env`

Never commit real credentials. `.env` is ignored by `.gitignore`.

## Quick Start

Create a starter scene file without calling an AI model:

```bash
python3 scripts/png_scene_scaffold.py input.png -o scene.json --canvas ppt169
```

Render a scene file to SVG:

```bash
python3 scripts/scene_to_svg.py scene.json -o slide_01.svg
```

Run an AI-assisted one-image conversion:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py auto input.png --project projects/demo --slide 1 --canvas ppt169
```

Run the deterministic build steps after SVG files already exist in `svg_output/`:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py build projects/demo
```

## Project Layout

The pipeline expects project folders shaped like this:

```text
project/
├── images/
├── scenes/
├── svg_output/
├── svg_final/
├── exports/
└── backup/
```

Generated project folders and PPTX exports are ignored by default.

## Repository Layout

- `SKILL.md`: Codex-facing workflow and trigger instructions.
- `agents/openai.yaml`: UI metadata for Codex skill lists.
- `references/`: detailed reconstruction, scene schema, and PPT compatibility notes.
- `scripts/`: local conversion, validation, SVG finalization, and PPTX export tools.
- `templates/icons/`: optional icon libraries for `<use data-icon="...">` placeholders.

## Notes for Sharing

Before publishing publicly, choose and add a license file that matches how you want others to reuse the code. Also confirm that no local `.env`, generated `projects/`, or exported `.pptx` files are included in the upload.
