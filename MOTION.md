---
schema: design-pipeline.motion-foundation.v0.1
name: AutoQuant Studio motion language
posture: static
primitiveRegistry: design-pipeline.motion-primitives.v1
---

## Motion Thesis

Research evidence should feel stable. Motion must never create a sense of price momentum, urgency or certainty. The product uses deliberate state changes and manual temporal navigation instead of decorative animation.

## Motion Principles

- A replay step changes the research time state; it is not a cinematic playback effect.
- State confirmation must be immediate and readable before any visual transition completes.
- The user can stop, step or jump at every point. No transition blocks evidence inspection or keyboard input.
- New data, revisions and failed tasks appear as labeled state changes, never as surprise animation.

## Motion Vocabulary

No registry primitive is selected. The static posture is intentional because the primary user work is analytical reading, comparison and audit.

## Procedural Motion

None. Charts and replay time progression are data render states, not procedural visual effects.

## Runtime Policy

Use semantic DOM and SVG for bounded visualizations. Small focus, hover and loading feedback may use CSS only if it preserves layout, can be interrupted and communicates no research meaning by itself. No GSAP, Anime.js, Canvas or GPU rendering runtime is selected by this foundation.

## Reduced Motion

The default posture already avoids continuous or decorative motion. The reduced-motion fallback keeps replay in manual-step mode, suppresses optional playback transitions and preserves focus, ordering, labels and error feedback.

## Source Decisions

- Adopted: a static, manual-step posture that treats replay as an inspectable research state.
- Rejected: animated market theatrics, continuous decorative loops and borrowed external motion implementations.
- This is an authored, requirements-only decision. No external motion implementation or visual reference was copied.
