---
name: toon-assemble
description: >-
  Assemble a cartoon scene from its approved takes for the toon pipeline: trim each take to its exact sequence length,
  join them in episode-plan order at one frame size and frame rate, make a contact sheet, and log the cut and the world
  state at the scene end in Archcore. Can also make a preview cut from drafts. Triggers: "assemble the scene",
  "cut the scene", "preview cut", "склей сцену", "собери сцену", "монтаж сцены", "черновая сборка".
metadata:
  author: alloself
  version: "0.1.0"
---

# toon-assemble

Every take is generated a little longer than its sequence. The model needs whole seconds and at least 4 of them, and the reference was padded by holding its last frame. Assembly trims every take back to the exact sequence length and joins the scene.

## Before you start

1. Read `toon.yaml`. See `../toon-setup/references/passport.md`. If it is missing, send the owner to `toon-setup` and stop.
2. Read the scene's sequences from the episode plan, in order, and each one's approved take from the scene log.
   - A normal cut uses finals.
   - A preview cut uses the latest approved or reviewed drafts, and only when the owner asks for one.
3. Talk in `series.language`.

## Steps

1. List the sequences with their take files.
   - If a sequence has no usable take, stop and name it.
   - For a preview cut, mark the sequence as a gap instead.
2. Read each sequence's exact length: `seconds` in its `sequence.json`.
3. Trim each take to its length:

   ```
   media.py fit <take> <tmp>/<sequence>.mp4 --seconds <seconds> --how trim
   ```

4. Join them at the series frame rate and the final size, using `series.aspect` and `higgsfield.resolution_final`, for example 1920x1080 for 16:9 at 1080p:

   ```
   media.py concat <output.cuts>/ep<NN>_<scene>_cut_v<N>.mp4 <tmp>/*.mp4 --fps <series.fps> --size <WxH>
   ```

   Pass the files in plan order, not in alphabetical order. Never overwrite an earlier cut: raise `v<N>` instead.
5. Run `media.py probe` on the cut. The duration must equal the sum of `seconds` within one frame.
6. Make `media.py sheet` of the cut, look at it, and check the joins between sequences for jumps.
7. Give the owner the cut path and the sheet path.

Audio is not part of v1: cuts are silent.

## Write Archcore

Follow `../toon-setup/references/archcore-conventions.md`.

- **Scene log:** the cut file, its version, the takes used, and any jumps found at joins.
- **World state at scene end:** fill it from the last take, if review has not.
- **Episode plan:** sequence and shot statuses set to `cut`, and the scene status updated.

Finish with the cut path, its length, the joins that need attention and the next scene in the plan.
