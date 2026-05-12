# AI Vision Configuration

Use this reference when the user wants PNG images decomposed by an AI vision model.

## Capability Boundary

AI vision can draft useful structured scene JSON from PNG slides. It is best at:

- Reading visible text and grouping it into titles, subtitles, labels, and body copy.
- Identifying panels, cards, buttons, badges, radar charts, nodes, connectors, and simple shapes.
- Planning which objects should become independent animation groups.
- Producing approximate coordinates in the target canvas.

AI vision is not reliable enough to perfectly recover:

- Original hidden PPT layers.
- Exact fonts, kerning, gradients, shadows, or particle effects.
- Complex character art, photos, soft focus, or exact vector paths.
- Exact chart data when the values are not explicitly visible.

Therefore the workflow uses AI for `scene JSON`, then deterministic Python renders and validates SVG.

## .env Locations

The AI script loads the first existing file from:

1. Current working directory `.env`
2. Skill directory `.env`
3. `~/.pngtosvgtoppt/.env`

## config.yaml

The AI script also reads `config.yaml` from the current working directory or the skill directory. The expected shape is:

```yaml
vision_provider:
  provider: openai
  base_url: https://api.openai.com/v1
  api_key_env: PNGTOSVGTOPPT_OPENAI_API_KEY
  model:
  timeout: 120
```

Command-line arguments override `.env`, and `.env` overrides missing fields from `config.yaml` where applicable.

## OpenAI-Compatible Backend

Use for OpenAI or providers that expose an OpenAI-compatible chat-completions API:

```bash
PNGTOSVGTOPPT_VISION_BACKEND=openai
PNGTOSVGTOPPT_OPENAI_API_KEY=...
PNGTOSVGTOPPT_OPENAI_MODEL=...
PNGTOSVGTOPPT_OPENAI_BASE_URL=https://api.openai.com/v1
```

For compatible providers, set `PNGTOSVGTOPPT_OPENAI_BASE_URL` to the provider endpoint and choose its vision-capable model.

## Gemini Backend

```bash
PNGTOSVGTOPPT_VISION_BACKEND=gemini
PNGTOSVGTOPPT_GEMINI_API_KEY=...
PNGTOSVGTOPPT_GEMINI_MODEL=...
PNGTOSVGTOPPT_GEMINI_BASE_URL=https://generativelanguage.googleapis.com
PNGTOSVGTOPPT_VISION_TIMEOUT=120
```

## Commands

Draft scene JSON:

```bash
python3 scripts/ai_vision_to_scene.py images/slide_01.png -o scenes/slide_01.scene.json --canvas ppt169 --source-href ../images/slide_01.png
```

Run the full automated conversion:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py auto images/slide_01.png --project projects/slide_01_rebuild --canvas ppt169
```

Write the prompt without calling a model:

```bash
python3 scripts/ai_vision_to_scene.py images/slide_01.png -o scenes/slide_01.scene.json --write-prompt prompt.txt
```

Validate scene JSON:

```bash
python3 scripts/scene_validate.py scenes/slide_01.scene.json
```
