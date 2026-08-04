# Change motion specification

- Project foundation: ../../../MOTION.md
- Foundation SHA-256: `aa65393e00df714613a2e9d39db47dbf990f299bc7b4cefae47ba2b8f5b443db`
- Foundation posture: static
- Selected primitive IDs: none

## Rules

- Replay step and jump update data immediately with no positional animation.
- Hover, focus, and press feedback use CSS transitions under 160 ms.
- Keyboard navigation has no animation.
- Optional playback is disabled under `prefers-reduced-motion`.
- Source transitions update labels and evidence atomically without hiding an
  unavailable or invalid state behind demo data.
