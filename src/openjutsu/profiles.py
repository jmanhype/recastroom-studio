# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field


IDENTITY_TEMPLATE = """<Subject 1> is the replacement performer shown in <Picture 1>. <Picture 2> is an additional authorized reference of the same performer and reinforces the same facial geometry, hair, skin tone, body proportions, and wardrobe.
The aligned guide and source audio are the temporal authority. The replacement performer must occupy only the selected target performer's position. All other people, foreground occluders, props, background elements, camera motion, lighting, and timing remain source-aligned."""


@dataclass
class RecastProfile:
    identity_description: str = IDENTITY_TEMPLATE
    preserve_statement: str = (
        "Preserve the source performer's posture, hands, arms, shoulders, head rotation, eye direction, "
        "eyelid aperture, mouth aperture, lip shapes, speech timing, and facial expression."
    )
    forbidden: list[str] = field(
        default_factory=lambda: [
            "unlicensed celebrity or public-figure likeness",
            "deceased performer recreation",
            "invented speech",
            "invented camera movement",
            "target-person bleeding into another person",
            "caramel or otherwise incorrect hair-color drift",
        ]
    )

    def render_prompt(self, word_schedule: str) -> str:
        forbidden = "\n".join(f"- {item}" for item in self.forbidden)
        return f"""body_swap:
subject_definitions:
{self.identity_description}

summary:
[video generation + reference + source audio] Replace only the selected target performer in the guide video with the authorized replacement performer while preserving the source performance and exact word schedule.

detailed_description:
The replacement performer takes the exact place of the selected target performer. {self.preserve_statement}
Use the source audio and the guide mouth as joint authority. Match jaw opening, lip rounding, labiodental contact, tongue-tip motion, chin movement, and micro-closures. Do not genericize speech into simple mouth ovals.

Exact word/frame schedule:
{word_schedule}

Integrate the replacement performer into the source's practical lighting and color temperature. Preserve the original room, props, camera, framing, background, and non-target people exactly. Prevent identity drift, hair-color drift, clothing changes, texture crawling, face flicker, invented gestures, extra speech, and temporal flicker.

forbidden:
{forbidden}

The result is real, photographic, and source-aligned."""
