---
name: toon-review
description: >-
  Review a generated cartoon take against its Blender reference and the series continuity rules. Puts reference and
  take frames side by side per shot and checks camera, cut timing, positions, scale, character count, props in hands,
  capsule or mannequin leaks, sliding or robotic motion, characters on model and the world state at the end. Gives a
  verdict (approved / regenerate with exact prompt changes / relayout) and, after the pilot, writes the
  reference-mode ADR. Triggers: "review the take", "check the generation", "compare with the layout", "pilot result",
  "проверь генерацию", "сравни с раскладкой", "оцени дубль", "итог пилота".
metadata:
  author: alloself
  version: "0.1.0"
---

# toon-review

A take is right when it keeps the plan and the characters look alive. The plan covers camera, cuts, who is where and at what size, and who holds what. This skill checks both against the reference and writes a verdict that `toon-sequence` can act on.

## Before you start

1. Read `toon.yaml`. See `../toon-setup/references/passport.md`. If it is missing, send the owner to `toon-setup` and stop.
2. Gather:
   - the take
   - its `sequence.json` and `ref_<mode>.mp4`
   - the prompt version used, from the scene log
   - the cards of the characters in frame
   - the `continuity` rule
3. Talk in `series.language`.

## 1. Measure

1. Run `media.py probe` on the take. Compare its length with the generated duration, and its size with what was ordered.
2. Pick times: each shot's middle, `(t0 + t1) / 2`, plus 0.1 s after every cut.
3. Run `media.py compare <ref> <take> <out.png> --at <times>`. It gives one row per time: reference on the left, take on the right.
4. Run `media.py sheet <take> <out.png> --cols 6 --rows 3` to see the motion.
5. Look at both images yourself. If motion is in doubt, add frames around that time with `media.py frames --every 0.25`.

## 2. Judge

Go through `references/checklist.md` item by item. For every failure, write the time, the shot and what is wrong. Do not judge style taste; judge against the plan and the cards.

## 3. Verdict

| Verdict | When | Hand-off |
|---|---|---|
| `approved` | No blocking failure | The owner confirms by watching the take: give the path. Then the status becomes `approved` |
| `regenerate` | Acting, props, on-model or leak failures the prompt can fix | Exact prompt changes per shot, following "Fixing a take" in `../toon-sequence/references/sequence-prompts.md` |
| `relayout` | Camera, cuts or positions are wrong because the layout is wrong, or stay wrong after two retries | What to change in Blender; the sequence goes back to `laid-out` |

An `approved` verdict needs the owner's yes. A `regenerate` inside the approved batch and retry limit needs no question.

## 4. Pilot

When the takes are a pilot comparison of reference modes on one sequence:

1. Score each mode with the checklist, side by side, as in the ADR template.
2. Answer the pilot questions from `../toon-setup/references/reference-modes.md`.
3. Recommend a winner, and let the owner pick.
4. Create `pipeline-reference-mode` from `../toon-setup/assets/archcore/reference-mode.adr.md`. Set it `accepted` after the owner's pick, and link it to `pipeline-approach` with `depends_on`.
5. Set `pipeline.reference_mode` in the passport, and update the pipeline guide.

## 5. Write Archcore

Follow `../toon-setup/references/archcore-conventions.md`.

- **Scene log, Takes table:** the verdict and its reasons, with the paths of the compare and sheet images.
- **Episode plan:** statuses for the sequence and its shots.
- **Last sequence of the scene approved:** fill World state at scene end from what the takes show.
- **New continuity rule:** if a failure reveals a rule that should hold everywhere, propose it to the owner. On yes, add it to `continuity` as a new clause.

Finish with the verdict, the reasons in one line each, and the next step.
