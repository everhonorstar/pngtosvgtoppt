#!/usr/bin/env python3
"""Render pngtosvgtoppt scene JSON into a PPT-safe SVG."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from scene_validate import SceneValidationError, normalize_scene


def attr(name: str, value: Any) -> str:
    if value is None:
        return ""
    return f' {name}="{html.escape(str(value), quote=True)}"'


def style_attrs(el: dict) -> str:
    mapping = {
        "fill": "fill",
        "stroke": "stroke",
        "stroke_width": "stroke-width",
        "fill_opacity": "fill-opacity",
        "stroke_opacity": "stroke-opacity",
        "opacity": "opacity",
        "font_size": "font-size",
        "font_family": "font-family",
        "font_weight": "font-weight",
        "text_decoration": "text-decoration",
    }
    return "".join(attr(svg_name, el.get(json_name)) for json_name, svg_name in mapping.items())


def render_element(el: dict, indent: int = 1) -> str:
    pad = "  " * indent
    typ = el.get("type")
    elem_id = el.get("id")

    if typ == "group":
        children = "\n".join(render_element(child, indent + 1) for child in el.get("children", []))
        return f"{pad}<g{attr('id', elem_id)}>\n{children}\n{pad}</g>"

    if typ == "rect":
        return (
            f"{pad}<rect{attr('id', elem_id)}{attr('x', el.get('x'))}{attr('y', el.get('y'))}"
            f"{attr('width', el.get('width'))}{attr('height', el.get('height'))}"
            f"{attr('rx', el.get('rx'))}{attr('ry', el.get('ry'))}{style_attrs(el)}/>"
        )

    if typ == "circle":
        return (
            f"{pad}<circle{attr('id', elem_id)}{attr('cx', el.get('cx'))}{attr('cy', el.get('cy'))}"
            f"{attr('r', el.get('r'))}{style_attrs(el)}/>"
        )

    if typ == "ellipse":
        return (
            f"{pad}<ellipse{attr('id', elem_id)}{attr('cx', el.get('cx'))}{attr('cy', el.get('cy'))}"
            f"{attr('rx', el.get('rx'))}{attr('ry', el.get('ry'))}{style_attrs(el)}/>"
        )

    if typ == "line":
        return (
            f"{pad}<line{attr('id', elem_id)}{attr('x1', el.get('x1'))}{attr('y1', el.get('y1'))}"
            f"{attr('x2', el.get('x2'))}{attr('y2', el.get('y2'))}{style_attrs(el)}/>"
        )

    if typ == "path":
        return f"{pad}<path{attr('id', elem_id)}{attr('d', el.get('d'))}{style_attrs(el)}/>"

    if typ == "polygon":
        return f"{pad}<polygon{attr('id', elem_id)}{attr('points', el.get('points'))}{style_attrs(el)}/>"

    if typ == "polyline":
        return f"{pad}<polyline{attr('id', elem_id)}{attr('points', el.get('points'))}{style_attrs(el)}/>"

    if typ == "text":
        text = html.escape(str(el.get("text", "")), quote=False)
        return (
            f"{pad}<text{attr('id', elem_id)}{attr('x', el.get('x'))}{attr('y', el.get('y'))}"
            f"{attr('text-anchor', el.get('anchor'))}{style_attrs(el)}>{text}</text>"
        )

    if typ == "image":
        preserve = el.get("preserve_aspect_ratio", "xMidYMid slice")
        return (
            f"{pad}<image{attr('id', elem_id)}{attr('href', el.get('href'))}"
            f"{attr('x', el.get('x'))}{attr('y', el.get('y'))}"
            f"{attr('width', el.get('width'))}{attr('height', el.get('height'))}"
            f"{attr('preserveAspectRatio', preserve)}/>"
        )

    raise SystemExit(f"Unsupported element type: {typ!r} in {elem_id!r}")


def render_svg(scene: dict) -> str:
    canvas = scene.get("canvas", {})
    width = int(canvas.get("width", 1280))
    height = int(canvas.get("height", 720))
    body = "\n".join(render_element(el) for el in scene.get("elements", []))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f"{body}\n"
        "</svg>\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a scene JSON file to PPT-safe SVG.")
    parser.add_argument("scene_json", help="Input scene JSON path")
    parser.add_argument("-o", "--output", required=True, help="Output SVG path")
    args = parser.parse_args()

    scene_path = Path(args.scene_json).expanduser()
    output_path = Path(args.output).expanduser()
    try:
        scene = normalize_scene(json.loads(scene_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, SceneValidationError) as exc:
        raise SystemExit(f"Scene invalid: {exc}") from exc
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_svg(scene), encoding="utf-8")
    print(f"Wrote SVG: {output_path}")


if __name__ == "__main__":
    main()
