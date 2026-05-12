#!/usr/bin/env python3
"""Create a starter scene JSON file for PNG-to-SVG reconstruction.

This script does not perform OCR or AI vision. It records image dimensions and
creates a conservative baked-background layer so an agent can add editable and
animatable elements deliberately.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


CANVASES = {
    "ppt169": (1280, 720),
    "ppt43": (1024, 768),
    "xhs": (1080, 1440),
    "story": (1080, 1920),
}


def rel_href(image_path: Path, output_path: Path) -> str:
    try:
        return image_path.resolve().relative_to(output_path.resolve().parent).as_posix()
    except ValueError:
        return image_path.as_posix()


def build_scene(image_path: Path, output_path: Path, canvas: str) -> dict:
    if canvas not in CANVASES:
        raise SystemExit(f"Unsupported canvas '{canvas}'. Options: {', '.join(CANVASES)}")

    with Image.open(image_path) as img:
        src_w, src_h = img.size

    canvas_w, canvas_h = CANVASES[canvas]
    href = rel_href(image_path, output_path)

    return {
        "version": "0.1",
        "canvas": {"preset": canvas, "width": canvas_w, "height": canvas_h},
        "source": {"image": href, "width": src_w, "height": src_h},
        "assessment": {
            "suitability_score": None,
            "recommended_mode": "hybrid",
            "notes": "Fill after visual/OCR assessment.",
        },
        "elements": [
            {
                "id": "background",
                "type": "group",
                "class": "Baked",
                "animatable": False,
                "children": [
                    {
                        "id": "background-image",
                        "type": "image",
                        "href": href,
                        "x": 0,
                        "y": 0,
                        "width": canvas_w,
                        "height": canvas_h,
                        "preserve_aspect_ratio": "xMidYMid slice",
                    }
                ],
            }
        ],
        "animation_plan": [],
        "review": {
            "needs_manual_layer_plan": True,
            "notes": "Add editable text, panels, charts, and isolated animation targets.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create starter scene JSON from a PNG/JPG image.")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("-o", "--output", required=True, help="Output scene JSON path")
    parser.add_argument("--canvas", default="ppt169", choices=sorted(CANVASES), help="Target canvas preset")
    args = parser.parse_args()

    image_path = Path(args.image).expanduser()
    output_path = Path(args.output).expanduser()
    if not image_path.exists():
        raise SystemExit(f"Input image does not exist: {image_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene = build_scene(image_path, output_path, args.canvas)
    output_path.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote scene scaffold: {output_path}")


if __name__ == "__main__":
    main()
