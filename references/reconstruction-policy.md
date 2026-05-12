# Reconstruction Policy

Use this file when judging a PNG slide or deciding how to split it into editable, animatable, and baked layers.

## Suitability Scores

Score each image from 1 to 5:

| Score | Meaning | Recommended Action |
|---|---|---|
| 5 | Mostly text, shapes, charts, panels, clear UI/infographic elements | Full structured SVG reconstruction |
| 4 | Strong structure plus some illustration/effects | Hybrid reconstruction with baked art layers |
| 3 | Mixed illustration and text; key content is clear | Rebuild editable overlays, bake most art |
| 2 | Mostly artwork/photo with limited editable content | Use as background, add minimal editable text |
| 1 | Photo/texture/painterly image with no clear structure | Do not structurally convert; keep as image |

## Layer Classes

### Editable

Use for content users are likely to revise:

- Titles, subtitles, body text, labels
- Buttons and CTA text
- Cards, panels, tables, badges
- Diagrams, radar charts, nodes, connectors
- Simple icons and status indicators

Rebuild as SVG text/shapes whenever legibility and location are clear.

### Animatable

Use for objects likely to receive entrance, emphasis, motion, or reveal effects:

- Main title and subtitle blocks
- Hero object, envelope, badge, trophy, character
- Chart groups, individual nodes, active node, check mark
- Mission card, glass panel, CTA button
- Light burst, star trail, magic ring, notification icon

Every animatable object must be an independent top-level `<g id="...">`. If an object is visually complex, keep it as an image but isolate it inside its own group.

### Baked

Use for elements where editability adds little value or reconstruction would damage fidelity:

- Photographic or illustrated backgrounds
- Soft-focus classroom scenes
- Characters with complex shading
- Dense particles, sparkles, glow fields
- Painterly shadows, depth-of-field, complex gradients

Baked layers should usually be one or more `<image>` elements. Avoid baking important text.

### Hybrid

Use when an element has both a complex visual body and editable labels. Example: keep a fancy panel glow as an image, then overlay editable text and a simplified border.

## Animation Planning Checklist

Before generating SVG, answer:

- What should enter first?
- What can be revealed step-by-step?
- Which objects should be selectable as one unit in PowerPoint?
- Which repeated elements need separate animation timing?
- Which effects are decorative and can stay baked?

## Classroom/Game Slide Defaults

For classroom hero-quest visuals:

- Keep classroom background as `background`.
- Rebuild major Chinese text as editable SVG text.
- Isolate student/character as `character-*` image group.
- Isolate envelope/trophy/badge as `hero-*` group.
- Rebuild radar charts as shapes whenever possible.
- Split nodes and labels into per-ability groups if the user may animate unlocking.
