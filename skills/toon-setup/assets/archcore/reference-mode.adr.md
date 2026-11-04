<!-- create_document type=adr, filename=pipeline-reference-mode, directory=series. Claims carry evidence: file paths, credits, frame times. -->
## Context

The Blender reference video carries camera, cuts and positions. Seedance copies the motion it sees, so the layout characters must not reach it as mannequins. The pilot compared reference modes on sequence <id>: <seconds> s, <shots> shots.

## Decision

Default reference mode: <capsule | frozen | hidden>. Per-sequence overrides stay allowed and are logged in the scene log.

## Alternatives

| Mode | Take | Camera | Cuts | Positions | Leaks | Acting | Grips | On model |
|---|---|---|---|---|---|---|---|---|
| capsule | <file> | <ok or issue> | | | | | | |
| frozen | <file> | | | | | | | |

## Consequences

<What changes in prompts or layout.>

Pilot answers:
- A final made from a draft keeps the draft's motion: <yes or no, evidence>.
- Cuts inside one generation are respected: <yes or no>.
- A close-up capsule is drawn as an object: <yes or no>.
- Reference video length limit: <seconds>.
