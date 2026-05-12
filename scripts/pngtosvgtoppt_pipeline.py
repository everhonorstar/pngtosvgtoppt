#!/usr/bin/env python3
"""Local pipeline wrapper for the pngtosvgtoppt skill."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CANVASES = {
    "ppt169": (1280, 720),
    "ppt43": (1024, 768),
    "xhs": (1080, 1440),
    "xiaohongshu": (1242, 1660),
    "story": (1080, 1920),
}


def run(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], check=True)


def ensure_project(project: Path) -> None:
    for name in ("images", "scenes", "svg_output", "svg_final", "exports", "backup"):
        (project / name).mkdir(parents=True, exist_ok=True)


def slide_stem(slide: int) -> str:
    return f"slide_{slide:02d}"


def cmd_scaffold(args: argparse.Namespace) -> None:
    project = args.project.expanduser()
    ensure_project(project)

    image_path = args.image.expanduser()
    if not image_path.exists():
        raise SystemExit(f"Input image does not exist: {image_path}")

    image_name = args.image_name or f"{slide_stem(args.slide)}{image_path.suffix.lower()}"
    target_image = project / "images" / image_name
    if image_path.resolve() != target_image.resolve():
        shutil.copy2(image_path, target_image)

    scene_path = project / "scenes" / f"{slide_stem(args.slide)}.scene.json"
    run([
        str(SCRIPT_DIR / "png_scene_scaffold.py"),
        str(target_image),
        "-o",
        str(scene_path),
        "--canvas",
        args.canvas,
    ])
    print(f"Scene scaffold: {scene_path}")


def cmd_render(args: argparse.Namespace) -> None:
    project = args.project.expanduser()
    ensure_project(project)
    scene_path = args.scene.expanduser()
    if not scene_path.exists():
        raise SystemExit(f"Scene JSON does not exist: {scene_path}")

    output = args.output
    if output is None:
        output = project / "svg_output" / f"{scene_path.stem.replace('.scene', '')}.svg"
    else:
        output = output.expanduser()

    run([str(SCRIPT_DIR / "scene_to_svg.py"), str(scene_path), "-o", str(output)])
    print(f"SVG output: {output}")


def cmd_ai_scene(args: argparse.Namespace) -> None:
    project = args.project.expanduser()
    ensure_project(project)

    image_path = args.image.expanduser()
    if not image_path.exists():
        raise SystemExit(f"Input image does not exist: {image_path}")

    image_name = args.image_name or f"{slide_stem(args.slide)}{image_path.suffix.lower()}"
    target_image = project / "images" / image_name
    if image_path.resolve() != target_image.resolve():
        shutil.copy2(image_path, target_image)

    scene_path = args.output.expanduser() if args.output else project / "scenes" / f"{slide_stem(args.slide)}.scene.json"
    source_href = f"../images/{image_name}"

    cmd = [
        str(SCRIPT_DIR / "ai_vision_to_scene.py"),
        str(target_image),
        "-o",
        str(scene_path),
        "--canvas",
        args.canvas,
        "--source-href",
        source_href,
    ]
    if args.backend:
        cmd.extend(["--backend", args.backend])
    if args.model:
        cmd.extend(["--model", args.model])
    if args.base_url:
        cmd.extend(["--base-url", args.base_url])
    if args.extra:
        cmd.extend(["--extra", args.extra])
    if args.write_prompt:
        cmd.extend(["--write-prompt", str(args.write_prompt.expanduser())])

    run(cmd)
    if args.write_prompt:
        print(f"AI prompt only: {args.write_prompt.expanduser()}")
    else:
        print(f"AI scene JSON: {scene_path}")


def cmd_check(args: argparse.Namespace) -> None:
    run([str(SCRIPT_DIR / "svg_quality_checker.py"), str(args.project.expanduser())])


def cmd_finalize(args: argparse.Namespace) -> None:
    cmd = [str(SCRIPT_DIR / "finalize_svg.py"), str(args.project.expanduser())]
    if args.quiet:
        cmd.append("--quiet")
    if args.compress:
        cmd.append("--compress")
    if args.max_dimension:
        cmd.extend(["--max-dimension", str(args.max_dimension)])
    run(cmd)


def cmd_export(args: argparse.Namespace) -> None:
    cmd = [str(SCRIPT_DIR / "svg_to_pptx.py"), str(args.project.expanduser())]
    if args.output:
        cmd.extend(["-o", str(args.output.expanduser())])
    if args.animation:
        cmd.extend(["-a", args.animation])
    if args.transition:
        cmd.extend(["-t", args.transition])
    run(cmd)


def cmd_build(args: argparse.Namespace) -> None:
    cmd_check(args)
    cmd_finalize(args)
    cmd_export(args)


def cmd_auto(args: argparse.Namespace) -> None:
    project = args.project.expanduser()
    ensure_project(project)

    image_path = args.image.expanduser()
    if not image_path.exists():
        raise SystemExit(f"Input image does not exist: {image_path}")

    image_name = args.image_name or f"{slide_stem(args.slide)}{image_path.suffix.lower()}"
    target_image = project / "images" / image_name
    if image_path.resolve() != target_image.resolve():
        shutil.copy2(image_path, target_image)

    scene_path = project / "scenes" / f"{slide_stem(args.slide)}.scene.json"
    svg_path = project / "svg_output" / f"{slide_stem(args.slide)}.svg"
    source_href = f"../images/{image_name}"

    ai_cmd = [
        str(SCRIPT_DIR / "ai_vision_to_scene.py"),
        str(target_image),
        "-o",
        str(scene_path),
        "--canvas",
        args.canvas,
        "--source-href",
        source_href,
    ]
    if args.backend:
        ai_cmd.extend(["--backend", args.backend])
    if args.model:
        ai_cmd.extend(["--model", args.model])
    if args.base_url:
        ai_cmd.extend(["--base-url", args.base_url])
    if args.extra:
        ai_cmd.extend(["--extra", args.extra])
    run(ai_cmd)

    run([str(SCRIPT_DIR / "scene_to_svg.py"), str(scene_path), "-o", str(svg_path)])
    run([str(SCRIPT_DIR / "svg_quality_checker.py"), str(project)])

    finalize_cmd = [str(SCRIPT_DIR / "finalize_svg.py"), str(project)]
    if args.quiet:
        finalize_cmd.append("--quiet")
    if args.compress:
        finalize_cmd.append("--compress")
    if args.max_dimension:
        finalize_cmd.extend(["--max-dimension", str(args.max_dimension)])
    run(finalize_cmd)

    export_cmd = [str(SCRIPT_DIR / "svg_to_pptx.py"), str(project)]
    if args.output:
        export_cmd.extend(["-o", str(args.output.expanduser())])
    if args.animation:
        export_cmd.extend(["-a", args.animation])
    if args.transition:
        export_cmd.extend(["-t", args.transition])
    run(export_cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="PNG-to-SVG-to-PPT local pipeline wrapper.")
    sub = parser.add_subparsers(dest="command", required=True)

    scaffold = sub.add_parser("scaffold", help="Create project folders and starter scene JSON from an image.")
    scaffold.add_argument("image", type=Path)
    scaffold.add_argument("--project", type=Path, required=True)
    scaffold.add_argument("--slide", type=int, default=1)
    scaffold.add_argument("--canvas", choices=sorted(CANVASES), default="ppt169")
    scaffold.add_argument("--image-name", default=None)
    scaffold.set_defaults(func=cmd_scaffold)

    render = sub.add_parser("render", help="Render one scene JSON into project/svg_output.")
    render.add_argument("scene", type=Path)
    render.add_argument("--project", type=Path, required=True)
    render.add_argument("-o", "--output", type=Path, default=None)
    render.set_defaults(func=cmd_render)

    ai_scene = sub.add_parser("ai-scene", help="Use a configured vision model to draft scene JSON from an image.")
    ai_scene.add_argument("image", type=Path)
    ai_scene.add_argument("--project", type=Path, required=True)
    ai_scene.add_argument("--slide", type=int, default=1)
    ai_scene.add_argument("--canvas", choices=sorted(CANVASES), default="ppt169")
    ai_scene.add_argument("--image-name", default=None)
    ai_scene.add_argument("-o", "--output", type=Path, default=None)
    ai_scene.add_argument("--backend", choices=["openai", "openai-compatible", "gemini"], default=None)
    ai_scene.add_argument("--model", default=None)
    ai_scene.add_argument("--base-url", default=None)
    ai_scene.add_argument("--extra", default="")
    ai_scene.add_argument("--write-prompt", type=Path, default=None)
    ai_scene.set_defaults(func=cmd_ai_scene)

    check = sub.add_parser("check", help="Run local SVG quality checker.")
    check.add_argument("project", type=Path)
    check.set_defaults(func=cmd_check)

    finalize = sub.add_parser("finalize", help="Run local SVG finalization.")
    finalize.add_argument("project", type=Path)
    finalize.add_argument("--quiet", action="store_true")
    finalize.add_argument("--compress", action="store_true")
    finalize.add_argument("--max-dimension", type=int, default=None)
    finalize.set_defaults(func=cmd_finalize)

    export = sub.add_parser("export", help="Export project SVGs to editable PPTX.")
    export.add_argument("project", type=Path)
    export.add_argument("-o", "--output", type=Path, default=None)
    export.add_argument("-a", "--animation", default=None)
    export.add_argument("-t", "--transition", default=None)
    export.set_defaults(func=cmd_export)

    build = sub.add_parser("build", help="Run check, finalize, and export in order.")
    build.add_argument("project", type=Path)
    build.add_argument("--quiet", action="store_true")
    build.add_argument("--compress", action="store_true")
    build.add_argument("--max-dimension", type=int, default=None)
    build.add_argument("-o", "--output", type=Path, default=None)
    build.add_argument("-a", "--animation", default=None)
    build.add_argument("-t", "--transition", default=None)
    build.set_defaults(func=cmd_build)

    auto = sub.add_parser("auto", help="Automatically run AI scene, render, check, finalize, and export for one image.")
    auto.add_argument("image", type=Path)
    auto.add_argument("--project", type=Path, required=True)
    auto.add_argument("--slide", type=int, default=1)
    auto.add_argument("--canvas", choices=sorted(CANVASES), default="ppt169")
    auto.add_argument("--image-name", default=None)
    auto.add_argument("--backend", choices=["openai", "openai-compatible", "gemini"], default=None)
    auto.add_argument("--model", default=None)
    auto.add_argument("--base-url", default=None)
    auto.add_argument("--extra", default="")
    auto.add_argument("--quiet", action="store_true")
    auto.add_argument("--compress", action="store_true")
    auto.add_argument("--max-dimension", type=int, default=None)
    auto.add_argument("-o", "--output", type=Path, default=None)
    auto.add_argument("-a", "--animation", default=None)
    auto.add_argument("-t", "--transition", default=None)
    auto.set_defaults(func=cmd_auto)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
