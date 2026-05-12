#!/usr/bin/env python3
"""Use a vision model to draft pngtosvgtoppt scene JSON from a PNG/JPG image."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import ssl
import sys
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image

from scene_validate import normalize_scene


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

CANVASES = {
    "ppt169": (1280, 720),
    "ppt43": (1024, 768),
    "xhs": (1080, 1440),
    "xiaohongshu": (1242, 1660),
    "story": (1080, 1920),
}


def load_yaml_config() -> dict[str, Any]:
    candidates = [
        Path.cwd() / "config.yaml",
        SKILL_DIR / "config.yaml",
    ]
    merged: dict[str, Any] = {}
    for path in candidates:
        if not path.exists():
            continue
        try:
            import yaml
        except ImportError:
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            for key, value in data.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = {**value, **merged[key]}
    return merged


def load_env() -> Path | None:
    candidates = [
        Path.cwd() / ".env",
        SKILL_DIR / ".env",
        Path.home() / ".pngtosvgtoppt" / ".env",
    ]
    loaded: Path | None = None
    for path in reversed(candidates):
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if path == Path.cwd() / ".env":
                os.environ[key] = value
            else:
                os.environ.setdefault(key, value)
        loaded = path
    return loaded


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def image_data_url(image_path: Path) -> tuple[str, str, int, int]:
    mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    with Image.open(image_path) as img:
        width, height = img.size
    return f"data:{mime};base64,{data}", mime, width, height


def extract_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


def redact_url(url: str) -> str:
    return re.sub(r"([?&]key=)[^&]+", r"\1[REDACTED]", url)


def default_ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        context = default_ssl_context()
        kwargs = {"timeout": timeout}
        if context is not None:
            kwargs["context"] = context
        with urllib.request.urlopen(req, **kwargs) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {redact_url(url)}: {body}") from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise RuntimeError(f"Request failed for {redact_url(url)}: {exc}") from exc


def build_prompt(canvas: str, canvas_w: int, canvas_h: int, source_href: str, extra: str = "") -> str:
    return f"""
You are reconstructing a flat slide image into structured scene JSON for editable PowerPoint export.

Return JSON only. No markdown.

Target canvas:
- preset: {canvas}
- width: {canvas_w}
- height: {canvas_h}

Source image href for baked background:
- {source_href}

Goal:
- Create a practical hybrid reconstruction, not a pixel-perfect vector trace.
- Always include a first top-level group with id "background" containing one full-canvas image using the source href.
- Rebuild important visible text as editable text elements.
- Rebuild simple panels, buttons, radar charts, nodes, connectors, borders, and labels as SVG-safe scene elements.
- Mark future animation targets as top-level groups with stable semantic ids.
- Use background/bg-* ids only for non-animated page chrome.
- Do not invent hidden content. If text is uncertain, set needs_review true.
- Avoid unsupported types. Use only group, rect, circle, ellipse, line, path, polygon, polyline, text, image.
- Use HEX colors or "none". Use Microsoft YaHei for Chinese text.

Scene JSON shape:
{{
  "version": "0.1",
  "canvas": {{"preset": "{canvas}", "width": {canvas_w}, "height": {canvas_h}}},
  "source": {{"image": "{source_href}"}},
  "assessment": {{
    "suitability_score": 1-5,
    "recommended_mode": "full-structured" | "hybrid" | "baked-with-overlays",
    "notes": "short explanation"
  }},
  "animation_plan": [
    {{"id": "title-main", "suggested_effect": "fade", "reason": "main title"}}
  ],
  "elements": [
    {{
      "id": "background",
      "type": "group",
      "class": "Baked",
      "animatable": false,
      "children": [
        {{"id": "background-image", "type": "image", "href": "{source_href}", "x": 0, "y": 0, "width": {canvas_w}, "height": {canvas_h}, "preserve_aspect_ratio": "xMidYMid slice"}}
      ]
    }}
  ]
}}

Style requirements:
- Use approximate positions in target canvas coordinates.
- Use top-level groups for title, subtitle, main panel, radar chart, each important radar node, CTA button, hero object, character, check mark, mission panel.
- If a complex object cannot be reconstructed, either leave it baked in the background or represent it with a simple editable proxy group.
- Keep text concise and faithful to the image.

Additional user instruction:
{extra or "(none)"}
""".strip()


def call_openai_compatible(
    image_url: str,
    prompt: str,
    model: str,
    api_key: str,
    base_url: str,
    timeout: int,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        "temperature": 0.1,
    }
    data = post_json(url, {"Authorization": f"Bearer {api_key}"}, payload, timeout)
    return data["choices"][0]["message"]["content"]


def call_gemini(
    image_b64: str,
    mime: str,
    prompt: str,
    model: str,
    api_key: str,
    base_url: str,
    timeout: int,
) -> str:
    url = f"{base_url.rstrip('/')}/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime, "data": image_b64}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.1},
    }
    data = post_json(url, {}, payload, timeout)
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(part.get("text", "") for part in parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft scene JSON from an image using a configured vision model.")
    parser.add_argument("image", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--canvas", choices=sorted(CANVASES), default="ppt169")
    parser.add_argument("--source-href", default=None, help="Href to use inside generated scene JSON, e.g. ../images/slide_01.png")
    parser.add_argument("--backend", choices=["openai", "openai-compatible", "gemini"], default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--extra", default="")
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument("--write-prompt", type=Path, default=None, help="Write the prompt and exit without calling a model.")
    args = parser.parse_args()

    env_path = load_env()
    config = load_yaml_config()
    vision_config = config.get("vision_provider", {}) if isinstance(config, dict) else {}
    if not isinstance(vision_config, dict):
        vision_config = {}

    image_path = args.image.expanduser()
    if not image_path.exists():
        raise SystemExit(f"Input image does not exist: {image_path}")

    data_url, mime, src_w, src_h = image_data_url(image_path)
    image_b64 = data_url.split(",", 1)[1]
    canvas_w, canvas_h = CANVASES[args.canvas]
    source_href = args.source_href or image_path.as_posix()
    prompt = build_prompt(args.canvas, canvas_w, canvas_h, source_href, args.extra)

    if args.write_prompt:
        args.write_prompt.write_text(prompt, encoding="utf-8")
        print(f"Wrote prompt: {args.write_prompt}")
        return

    backend = args.backend or os.environ.get("PNGTOSVGTOPPT_VISION_BACKEND") or vision_config.get("provider")
    if not backend:
        raise SystemExit(
            "No vision backend configured. Set PNGTOSVGTOPPT_VISION_BACKEND=openai, "
            "openai-compatible, or gemini in .env, or pass --backend."
        )

    if backend in {"openai", "openai-compatible"}:
        key_env = vision_config.get("api_key_env") if vision_config.get("provider") in {"openai", "openai-compatible"} else None
        api_key = args.api_key or os.environ.get("PNGTOSVGTOPPT_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") or (os.environ.get(str(key_env)) if key_env else None)
        model = args.model or os.environ.get("PNGTOSVGTOPPT_OPENAI_MODEL") or os.environ.get("OPENAI_MODEL") or (vision_config.get("model") if vision_config.get("provider") in {"openai", "openai-compatible"} else None)
        base_url = args.base_url or os.environ.get("PNGTOSVGTOPPT_OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or (vision_config.get("base_url") if vision_config.get("provider") in {"openai", "openai-compatible"} else None) or "https://api.openai.com/v1"
        timeout = args.timeout or env_int("PNGTOSVGTOPPT_VISION_TIMEOUT", int(vision_config.get("timeout") or 180))
        if not api_key or not model:
            raise SystemExit("OpenAI-compatible backend requires API key and model. Set PNGTOSVGTOPPT_OPENAI_API_KEY and PNGTOSVGTOPPT_OPENAI_MODEL.")
        try:
            content = call_openai_compatible(data_url, prompt, model, api_key, base_url, timeout)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
    elif backend == "gemini":
        key_env = vision_config.get("api_key_env") if vision_config.get("provider") == "gemini" else None
        api_key = args.api_key or os.environ.get("PNGTOSVGTOPPT_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") or (os.environ.get(str(key_env)) if key_env else None)
        model = args.model or os.environ.get("PNGTOSVGTOPPT_GEMINI_MODEL") or os.environ.get("GEMINI_MODEL") or (vision_config.get("model") if vision_config.get("provider") == "gemini" else None)
        base_url = args.base_url or os.environ.get("PNGTOSVGTOPPT_GEMINI_BASE_URL") or os.environ.get("GEMINI_BASE_URL") or (vision_config.get("base_url") if vision_config.get("provider") == "gemini" else None) or "https://generativelanguage.googleapis.com"
        timeout = args.timeout or env_int("PNGTOSVGTOPPT_VISION_TIMEOUT", int(vision_config.get("timeout") or 180))
        if not api_key or not model:
            raise SystemExit("Gemini backend requires API key and model. Set PNGTOSVGTOPPT_GEMINI_API_KEY and PNGTOSVGTOPPT_GEMINI_MODEL.")
        try:
            content = call_gemini(image_b64, mime, prompt, model, api_key, base_url, timeout)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        raise SystemExit(f"Unsupported backend: {backend}")

    scene = extract_json(content)
    scene.setdefault("source", {})
    scene["source"].setdefault("image", source_href)
    scene["source"].setdefault("width", src_w)
    scene["source"].setdefault("height", src_h)
    normalized = normalize_scene(scene)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    source_note = f" using {env_path}" if env_path else ""
    print(f"Wrote AI scene JSON: {args.output}{source_note}")


if __name__ == "__main__":
    main()
