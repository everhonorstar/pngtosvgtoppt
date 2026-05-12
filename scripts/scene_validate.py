#!/usr/bin/env python3
"""Validate and lightly normalize pngtosvgtoppt scene JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {
    "group",
    "rect",
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "text",
    "image",
}

REQUIRED_FIELDS = {
    "group": ("children",),
    "rect": ("x", "y", "width", "height"),
    "circle": ("cx", "cy", "r"),
    "ellipse": ("cx", "cy", "rx", "ry"),
    "line": ("x1", "y1", "x2", "y2"),
    "path": ("d",),
    "polygon": ("points",),
    "polyline": ("points",),
    "text": ("x", "y", "text"),
    "image": ("href", "x", "y", "width", "height"),
}

DEFAULTS = {
    "rect": {"fill": "#FFFFFF", "stroke": "none"},
    "circle": {"fill": "#FFFFFF", "stroke": "none"},
    "ellipse": {"fill": "#FFFFFF", "stroke": "none"},
    "line": {"stroke": "#000000", "stroke_width": 1},
    "path": {"fill": "none", "stroke": "#000000", "stroke_width": 1},
    "polygon": {"fill": "#FFFFFF", "stroke": "none"},
    "polyline": {"fill": "none", "stroke": "#000000", "stroke_width": 1},
    "text": {
        "font_family": "Microsoft YaHei",
        "font_size": 24,
        "fill": "#111111",
    },
    "image": {"preserve_aspect_ratio": "xMidYMid slice"},
}

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{3,8}$")
ID_RE = re.compile(r"[^a-zA-Z0-9_-]+")


class SceneValidationError(Exception):
    pass


def safe_id(raw: Any, fallback: str) -> str:
    text = str(raw or fallback).strip().replace(" ", "-")
    text = ID_RE.sub("-", text).strip("-").lower()
    return text or fallback


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SceneValidationError(message)


def normalize_number(value: Any, path: str) -> int | float:
    if isinstance(value, bool):
        raise SceneValidationError(f"{path}: expected number, got bool")
    if isinstance(value, (int, float)):
        return value
    try:
        num = float(str(value).strip())
    except Exception as exc:
        raise SceneValidationError(f"{path}: expected number, got {value!r}") from exc
    return int(num) if num.is_integer() else num


def normalize_style(el: dict, path: str) -> None:
    for key, value in list(el.items()):
        if key in {"x", "y", "width", "height", "rx", "ry", "cx", "cy", "r", "x1", "y1", "x2", "y2", "font_size", "stroke_width", "fill_opacity", "stroke_opacity", "opacity"} and value is not None:
            el[key] = normalize_number(value, f"{path}.{key}")
        if key in {"fill", "stroke"} and isinstance(value, str):
            if value.lower() in {"none", "transparent"}:
                if value.lower() == "transparent":
                    el[key] = "none"
                continue
            require(bool(HEX_RE.match(value)), f"{path}.{key}: use HEX colors or 'none', got {value!r}")


def normalize_element(el: Any, path: str, index: int = 0) -> dict:
    require(isinstance(el, dict), f"{path}: element must be an object")
    typ = el.get("type")
    require(typ in ALLOWED_TYPES, f"{path}: unsupported element type {typ!r}")

    out = dict(el)
    out["id"] = safe_id(out.get("id"), f"{typ}-{index}")
    for key, value in DEFAULTS.get(typ, {}).items():
        out.setdefault(key, value)

    for field in REQUIRED_FIELDS[typ]:
        require(field in out, f"{path}.{out['id']}: missing required field {field!r}")

    if typ == "group":
        children = out.get("children")
        require(isinstance(children, list), f"{path}.{out['id']}.children must be a list")
        out["children"] = [
            normalize_element(child, f"{path}.{out['id']}.children[{i}]", i)
            for i, child in enumerate(children)
        ]
    else:
        normalize_style(out, f"{path}.{out['id']}")

    return out


def normalize_scene(scene: dict) -> dict:
    require(isinstance(scene, dict), "scene must be an object")
    canvas = scene.setdefault("canvas", {})
    require(isinstance(canvas, dict), "canvas must be an object")
    canvas.setdefault("preset", "ppt169")
    canvas["width"] = int(normalize_number(canvas.get("width", 1280), "canvas.width"))
    canvas["height"] = int(normalize_number(canvas.get("height", 720), "canvas.height"))
    require(canvas["width"] > 0 and canvas["height"] > 0, "canvas dimensions must be positive")

    scene.setdefault("version", "0.1")
    scene.setdefault("assessment", {})
    scene.setdefault("source", {})
    elements = scene.get("elements")
    require(isinstance(elements, list), "elements must be a list")
    scene["elements"] = [normalize_element(el, f"elements[{i}]", i) for i, el in enumerate(elements)]
    return scene


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and normalize scene JSON.")
    parser.add_argument("scene_json", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        scene = json.loads(args.scene_json.read_text(encoding="utf-8"))
        normalized = normalize_scene(scene)
    except (json.JSONDecodeError, SceneValidationError) as exc:
        raise SystemExit(f"Scene invalid: {exc}") from exc
    out = args.output or args.scene_json
    out.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Scene valid: {out}")


if __name__ == "__main__":
    main()
