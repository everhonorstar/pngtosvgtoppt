# Embedded PPT Pipeline

This skill carries its own copy of the mature SVG validation, finalization, and PPTX export pipeline. Use these local scripts instead of invoking another skill.

## Project Layout

Expected project layout:

```text
project/
├── images/
├── scenes/
├── svg_output/
├── svg_final/
├── exports/
└── backup/
```

Only `svg_output/` is required before check/finalize/export. `images/` is required if SVGs reference baked bitmap layers.

## Commands

Run commands from the skill directory:

```bash
python3 scripts/svg_quality_checker.py <project>
python3 scripts/finalize_svg.py <project>
python3 scripts/svg_to_pptx.py <project>
```

Or use the wrapper:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py build <project>
```

For a single PNG image, use the automatic wrapper:

```bash
python3 scripts/pngtosvgtoppt_pipeline.py auto input.png --project <project> --canvas ppt169
```

`auto` runs AI decomposition, scene rendering, quality checking, SVG finalization, and PPTX export without requiring manual subcommands.

## Export Behavior

`svg_to_pptx.py` creates:

- `exports/<project>_<timestamp>.pptx`: editable native PowerPoint shapes
- `backup/<timestamp>/<project>_svg.pptx`: SVG preview fallback
- `backup/<timestamp>/svg_output/`: source SVG snapshot

## Notes

- Native PPTX reads from `svg_output/` so it can preserve editable primitives.
- Preview PPTX reads from `svg_final/`.
- Keep top-level `<g id="...">` groups for animation targets.
- Avoid `<use data-icon="...">` unless the matching icon library exists under `templates/icons/`.
