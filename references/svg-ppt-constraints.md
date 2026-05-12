# SVG/PPT Constraints

Use this file when turning scene JSON into SVG for this skill's bundled SVG-to-PPTX export.

## Allowed SVG Elements

Use:

- `<svg>`
- `<defs>` for gradients, markers, and image clip paths
- `<g>`
- `<rect>`
- `<circle>`
- `<ellipse>`
- `<line>`
- `<path>`
- `<polygon>`
- `<polyline>`
- `<text>` and simple `<tspan>`
- `<image>`

Avoid advanced SVG features unless the downstream converter explicitly supports them.

## Hard Rules

- Use a `viewBox` matching the canvas.
- Use inline attributes, not CSS classes or `<style>`.
- Use hex colors and `fill-opacity` / `stroke-opacity`; do not use `rgba(...)`.
- Do not use `<foreignObject>`, masks, scripts, animations, textPath, or custom fonts.
- Use top-level `<g id="...">` for semantic and animation layers. The local converter records these as animation targets.
- Keep important text as `<text>`, not inside raster images.
- Use `<image href="../images/name.png" preserveAspectRatio="xMidYMid slice">` for baked layers.

## Text Rules

- Use `font-family` with installed fallback fonts such as `Microsoft YaHei`, `SimSun`, `Arial`, or `Times New Roman`.
- For one logical line, use one `<text>` element.
- Use separate `<text>` elements for separate blocks or columns.
- Escape XML reserved characters: `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`.

## Animation Group Ids

Good ids:

- `title-main`
- `subtitle`
- `hero-envelope`
- `radar-chart`
- `radar-node-responsibility`
- `character-student`
- `mission-panel`
- `cta-button`

Background/page chrome ids:

- `background`
- `bg-classroom`
- `footer`
- `watermark`

## Baked Image Policy

Baked image layers are allowed, but isolate them if they may animate. Example:

```xml
<g id="character-student">
  <image href="../images/student.png" x="880" y="150" width="260" height="360"
         preserveAspectRatio="xMidYMid meet"/>
</g>
```

This keeps the character selectable and animatable even if it is not structurally editable.
