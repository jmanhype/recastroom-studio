# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowCard:
    id: str
    name: str
    status: str
    summary: str
    description: str
    model: str
    available: bool
    action: str
    badges: tuple[str, ...]


CARDS: tuple[WorkflowCard, ...] = (
    WorkflowCard(
        id="recast-room",
        name="Recast Room",
        status="Production",
        summary="Same performance. New lead.",
        description=(
            "Replace the selected performer while preserving the source take, camera, "
            "scene, timing, and dialogue."
        ),
        model="MiniMax H3 Ref2VA",
        available=True,
        action="Open workflow",
        badges=("Character Swap v1.1", "SAM 3.1", "Exact audio lock"),
    ),
    WorkflowCard(
        id="custom-recast",
        name="Custom Recast Graph",
        status="Advanced",
        summary="Bring your own C1-compatible graph.",
        description=(
            "Import a RecastRoom-compatible Comfy API workflow and run it through "
            "the same operator attestation gate, preflight, review, and artifact path."
        ),
        model="Your MiniMax H3 graph",
        available=True,
        action="Import JSON",
        badges=("Comfy API format", "Pinned inputs", "Attestation gate"),
    ),
    WorkflowCard(
        id="multi-person-recast",
        name="Multi-Person Recast",
        status="Concept",
        summary="More cast. Same boundaries.",
        description=(
            "A planned engine for assigning separate references, masks, permission records, "
            "and QC reports to multiple performers in one source take."
        ),
        model="Planned MiniMax H3 engine",
        available=False,
        action="Roadmap",
        badges=("Per-person consent", "Per-person QC", "Not in this release"),
    ),
    WorkflowCard(
        id="studio-queue",
        name="Studio Queue",
        status="Concept",
        summary="Take-level production state.",
        description=(
            "A planned queue for take history, rerenders, provenance, and review status "
            "across a production without turning RecastRoom into a generic video studio."
        ),
        model="Planned",
        available=False,
        action="Roadmap",
        badges=("Take provenance", "Rerender control", "Not in this release"),
    ),
    WorkflowCard(
        id="cinematic-camera",
        name="Cinematic Camera",
        status="Concept",
        summary="Direct lens, light, and movement.",
        description="A planned studio lane for camera-language presets on a selected shot.",
        model="Planned",
        available=False,
        action="Roadmap",
        badges=("Not in this release",),
    ),
    WorkflowCard(
        id="re-shoot",
        name="Re-Shoot",
        status="Concept",
        summary="New angle. Same moment.",
        description="A planned lane for preserving a performance while changing viewpoint.",
        model="Planned",
        available=False,
        action="Roadmap",
        badges=("Not in this release",),
    ),
    WorkflowCard(
        id="vfx-presets",
        name="VFX Presets",
        status="Concept",
        summary="One take. Many looks.",
        description="A planned lane for reusable, remixable visual-effect recipes.",
        model="Planned",
        available=False,
        action="Roadmap",
        badges=("Not in this release",),
    ),
)


def catalog() -> dict[str, Any]:
    return {
        "studio": {
            "name": "RecastRoom Studio",
            "tagline": "An open creative workspace for performance-preserving video workflows.",
        },
        "workflows": [{**asdict(card), "badges": list(card.badges)} for card in CARDS],
    }
