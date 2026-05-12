"""Minimal PowerPoint OOXML animation and transition helpers.

The SVG-to-PPTX pipeline imports this module as an optional dependency. Keeping
it bundled makes the public skill honor its exposed transition and per-group
animation flags instead of silently degrading to static slides.
"""

from __future__ import annotations

import itertools
import random
from typing import Iterable


TRANSITIONS = {
    "fade": {"name": "Fade"},
    "push": {"name": "Push"},
    "wipe": {"name": "Wipe"},
    "split": {"name": "Split"},
    "strips": {"name": "Strips"},
    "cover": {"name": "Cover"},
    "random": {"name": "Random"},
}

ANIMATIONS = {
    "appear": {"name": "Appear"},
    "fade": {"name": "Fade"},
    "fly": {"name": "Fly In"},
    "zoom": {"name": "Zoom"},
}

_MIXED_SEQUENCE = ("fade", "fly", "zoom", "appear")


def _escape_attr(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _effect_xml(effect: str, shape_id: int, duration_ms: int, delay_ms: int) -> str:
    """Return a single entrance animation node for one shape id."""
    preset_map = {
        "appear": ("entr", "1"),
        "fade": ("entr", "10"),
        "fly": ("entr", "2"),
        "zoom": ("entr", "50"),
    }
    preset_class, preset_id = preset_map.get(effect, preset_map["fade"])
    delay = max(0, int(delay_ms))
    duration = max(1, int(duration_ms))
    shape_ref = _escape_attr(shape_id)
    node_id = 1000 + int(shape_id)
    return f"""
<p:par>
  <p:cTn id="{node_id}" dur="indefinite" restart="never" nodeType="clickEffect">
    <p:stCondLst>
      <p:cond delay="{delay}"/>
    </p:stCondLst>
    <p:childTnLst>
      <p:par>
        <p:cTn id="{node_id + 100000}" presetID="{preset_id}" presetClass="{preset_class}" presetSubtype="0" fill="hold">
          <p:stCondLst>
            <p:cond delay="0"/>
          </p:stCondLst>
          <p:childTnLst>
            <p:set>
              <p:cBhvr>
                <p:cTn id="{node_id + 200000}" dur="1" fill="hold"/>
                <p:tgtEl>
                  <p:spTgt spid="{shape_ref}"/>
                </p:tgtEl>
                <p:attrNameLst>
                  <p:attrName>style.visibility</p:attrName>
                </p:attrNameLst>
              </p:cBhvr>
              <p:to>
                <p:strVal val="visible"/>
              </p:to>
            </p:set>
            <p:animEffect transition="in" filter="{_escape_attr(effect)}">
              <p:cBhvr>
                <p:cTn id="{node_id + 300000}" dur="{duration}" fill="hold"/>
                <p:tgtEl>
                  <p:spTgt spid="{shape_ref}"/>
                </p:tgtEl>
              </p:cBhvr>
            </p:animEffect>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:childTnLst>
  </p:cTn>
</p:par>""".strip()


def pick_animation_effect(mode: str | None, index: int, offset: int = 0) -> str:
    """Choose a concrete animation effect for a requested mode."""
    if mode in ANIMATIONS:
        return str(mode)
    if mode == "random":
        return random.choice(tuple(ANIMATIONS.keys()))
    if mode == "mixed" or not mode:
        return _MIXED_SEQUENCE[(index + offset) % len(_MIXED_SEQUENCE)]
    return "fade"


def create_sequence_timing_xml(
    targets: Iterable[tuple[int | list[int] | tuple[int, ...], int, str]],
    *,
    duration: float = 0.4,
    trigger: str = "after-previous",
) -> str:
    """Create PowerPoint timing XML for entrance animations.

    ``targets`` contains ``(shape_ids, delay_ms, effect)`` tuples. ``shape_ids``
    may be a single id or a list, allowing semantic SVG groups to animate their
    child shapes in the same step.
    """
    duration_ms = int(max(0.01, duration) * 1000)
    trigger = trigger if trigger in {"on-click", "with-previous", "after-previous"} else "after-previous"

    effect_nodes: list[str] = []
    flat_index = 0
    for shape_ids, delay_ms, effect in targets:
        ids = shape_ids if isinstance(shape_ids, (list, tuple)) else [shape_ids]
        for shape_id in ids:
            if trigger == "with-previous":
                actual_delay = 0
            elif trigger == "on-click":
                actual_delay = 0
            else:
                actual_delay = delay_ms
            effect_nodes.append(_effect_xml(effect, int(shape_id), duration_ms, actual_delay))
            flat_index += 1

    if not effect_nodes:
        return ""

    first_condition = "onClick" if trigger == "on-click" else "withPrev"
    return f"""
<p:timing>
  <p:tnLst>
    <p:par>
      <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
        <p:childTnLst>
          <p:seq concurrent="1" nextAc="seek">
            <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
              <p:stCondLst>
                <p:cond evt="{first_condition}" delay="0"/>
              </p:stCondLst>
              <p:childTnLst>
                {''.join(effect_nodes)}
              </p:childTnLst>
            </p:cTn>
          </p:seq>
        </p:childTnLst>
      </p:cTn>
    </p:par>
  </p:tnLst>
</p:timing>""".strip()


def create_transition_xml(
    effect: str = "fade",
    duration: float = 0.5,
    advance_after: float | None = None,
) -> str:
    """Create a slide transition XML fragment."""
    effect = effect if effect in TRANSITIONS else "fade"
    speed = "fast" if duration <= 0.4 else "med" if duration <= 0.9 else "slow"
    adv_attr = ""
    if advance_after is not None:
        adv_attr = f' advTm="{int(max(0, advance_after) * 1000)}"'

    child_map = {
        "fade": '<p:fade/>',
        "push": '<p:push dir="l"/>',
        "wipe": '<p:wipe dir="l"/>',
        "split": '<p:split orient="horz" dir="out"/>',
        "strips": '<p:strips dir="ld"/>',
        "cover": '<p:cover dir="l"/>',
        "random": '<p:random/>',
    }
    return f'<p:transition spd="{speed}"{adv_attr}>{child_map[effect]}</p:transition>'

