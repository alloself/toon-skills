# Reference modes

Seedance copies what it sees in a reference video. A layout mannequin that slides and moves stiffly comes back as a character that slides and moves stiffly, and hands copied from a blockout grip things badly. So the Blender reference must carry only what Blender is good at: camera, cuts, perspective, environment scale, and where each character is and how big. The acting comes from the character sheets and the text.

## What goes into one generation

| Input | Source | Carries |
|---|---|---|
| Video reference | Blender, one render per sequence, characters replaced by capsules | camera moves, cut points, framing, positions, paths, relative scale, props |
| Image references | `toon-bible` cards | how each character looks from every side; how each location looks |
| Optional state image | last frame of the previous approved take, only at a sticky boundary | what the world looked like when the previous sequence ended |
| Prompt | `toon-sequence` | shot-by-shot timeline: camera in words, who does what, emotions, turns, grips, colour legend |

There are no keyframes and no start frames. A start frame freezes the first pose and the camera, so characters cannot turn and the camera cannot move. Generating one per shot also costs credits and time.

## Modes

| Mode | Characters in the reference | Use |
|---|---|---|
| `capsule` | A coloured capsule per character, as tall as the character, on its root path. It is visible exactly when the character is | Default. Positions and paths survive, and there are no limbs to copy |
| `frozen` | The layout characters held still in their first-frame pose; the camera still moves | Pilot comparison. Gives silhouettes but no paths |
| `hidden` | None; only environment, props and camera | When capsules confuse the model; positions then come from text only |
| `full` | Everything as animated in Blender | Never for generation; only to show the owner the layout |

Props stay visible in every mode unless `pipeline.props` is `hide`. A plank moving beside the red capsule tells the model where the plank goes; the prompt says who holds it and how.

## Colour legend

Capsule colours come from `legend` in `sequence.json`. Pass `char_order` in passport order, so each character keeps one colour for the whole series: the first is red, then blue, yellow, green, purple, cyan, orange and white. The prompt always includes the legend for the characters in frame:

```
The coloured capsules in the reference video are placeholders, not objects:
red = Fox (image 1), blue = Owl (image 2). Keep their positions, paths and size in frame.
Draw the characters from their reference images and invent their acting from the text.
```

In close-ups a capsule fills most of the frame. The reference then says only whose close-up it is and where the head is, so the text must carry the face, the emotion and the hands.

## Pilot: choosing the default

Run once per series, on one sequence of 8 to 12 seconds. Pick one with two characters, a camera move, a cut to a close-up, and a prop in hand.

1. `toon-layout` exports the sequence with `modes: ["capsule", "frozen"]`.
2. `toon-sequence` generates one draft per mode with the same prompt, sheets and plates, under one approval.
3. `toon-review` scores both drafts with `toon-review/references/checklist.md`:
   - camera follows the reference
   - cuts land on time
   - positions and scale match
   - no capsule or mannequin leaks into the picture
   - acting looks alive, not robotic
   - grips look plausible
   - characters stay on model
4. The owner picks the winner. `toon-review` writes `pipeline-reference-mode.adr.md` and sets `pipeline.reference_mode`.
5. The pilot also answers these questions; record the answers in the ADR:
   - Does a finished take made from a draft via `draft_job_id` keep the draft's motion?
   - Does the model respect cuts inside one generation?
   - Does it treat a full-frame capsule in a close-up as a solid object?
   - Is the reference video length limit at least `pipeline.sequence_max`?

If the model draws capsules as real objects in both modes, try `hidden` with positions spelled out in the prompt from the cast boxes, for example "Fox on the left third, full height, walking toward camera".

## Per-sequence overrides

The ADR sets the default. A sequence can still use another mode, for example `frozen` when a pose matters more than a path. Record the override and the reason in the scene log.
