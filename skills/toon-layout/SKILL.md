---
name: toon-layout
description: >-
  Read a Blender layout for the toon pipeline and turn it into Seedance references: check shot markers, cameras,
  characters, props and unmarked moving objects; run the continuity check; propose sequences (several consecutive
  shots per Seedance 2.5 generation, 4-30 s) and agree them with the owner; export one reference video per sequence
  with characters as coloured capsules, plus sequence.json with cuts, camera moves and cast. Never saves or edits the
  .blend. Triggers: "check the layout", "export references", "cut the scene into sequences", "blender layout",
  "проверь раскладку", "нарежь на секвенции", "выгрузи референсы", "референс из блендера".
metadata:
  author: alloself
  version: "0.1.0"
---

# toon-layout

Blender is the plan: positions, scale, camera and cuts. This skill checks that plan and exports it in a form that carries no robotic acting. Characters become coloured capsules on their paths, props stay visible, and the camera and cuts stay exactly as laid out.

## Before you start

1. Read `toon.yaml`. See `../toon-setup/references/passport.md`. If it is missing, send the owner to `toon-setup` and stop.
2. Read `../toon-setup/references/blender-conventions.md`. It defines the module, its commands and how to call it over an MCP or headless.
3. Make sure the module answers `version`. Install it if not.
4. Build the settings you pass to every call:
   - `char_prefix`, `prop_prefix`, `camera_prefix`, `seq_prefix`, `char_names`, `prop_names` and `marker_regex` from `blender`
   - `jump_m` from `pipeline`
   - `aspect` from `series`
   - `char_order`: the `characters[].blender` names in passport order
5. Talk in `series.language`.

## 1. Check the file

Run `check` with `max_shot_seconds` set to `pipeline.sequence_max` and `min_shot_seconds` set to `pipeline.min_shot_seconds`. Report the result as a short list.

- **Errors** block the export. Explain the fix in Blender terms, for example "bind a camera to marker X: select the camera, playhead on the marker, Marker > Bind Camera to Markers".
- **Travellers** are objects that move but are neither characters nor props. Ask the owner about them in one question, recommending from `looks_like`. Write the answers to `blender.char_names` or `blender.prop_names` in the passport.
- Other warnings, such as unparsed names, very short or long shots and a wrong aspect, go to the owner once, with a recommendation.

## 2. Continuity

Run `continuity` for the scene with `inside=True`. For each visible jump, ask whether it is intended:
- If it is a time skip, note it in the episode plan.
- If it is a layout mistake, list it as a fix for the owner.

Write findings to the scene log, under Continuity findings.

## 3. Shots and plan

Run `shots` for the scene with `camera=True` and `cast=True`. If the episode plan exists, reconcile it as `toon-episode` mode B does and set laid-out shots to `laid-out`. If there is no plan, offer to create it from the layout.

## 4. Sequences

1. Run `sequences` with:
   - `scene`
   - `target` set to `pipeline.sequence_target`
   - `max_seconds` set to `pipeline.sequence_max`
   - `min_seconds` set to `pipeline.sequence_min`
2. Show them as a table: sequence, shots, seconds, cast, why it ends. Mark the boundaries of type `length`: they may cut through an action.
3. Ask one question: accept, or edit in words, for example "merge B and C", "split before shot 14" or "C is sticky". Apply and show again until the owner accepts. Every sequence must be consecutive shots of one scene, at most `sequence_max` seconds long.
4. A sticky sequence waits for the approved take of the one before it and gets that take's last frame as a state image. Ask about each `length` boundary. Recommend sticky when the same action continues across the cut.
5. Write the agreed sequences into the episode plan and the scene log, with status `planned` and the sticky flags.

## 5. Export references

1. Pick the mode.
   - Without an accepted `pipeline-reference-mode` ADR, this is the pilot. Export the chosen pilot sequence with `modes: ["capsule", "frozen"]`, see `../toon-setup/references/reference-modes.md`.
   - Otherwise, use `pipeline.reference_mode` unless the scene log records an override for that sequence.
2. Run `export` with:
   - `sequences`: the agreed list
   - `out` set to `blender.exchange_dir`
   - `props` set to `pipeline.props`
   - the settings from "Before you start"
3. Through an MCP, poll `status` until `done` or `error`. Headless, the call returns when the render is done. On `error`, report the first lines of the error and the job's `_worker.log`. Do not retry blindly.
4. Read the results from `blender.exchange_dir_local`:
   - `sequence.json` per sequence
   - `ref_<mode>.mp4`, checked with `../toon-setup/scripts/media.py probe`. Its length must match `seconds`
5. Make a contact sheet with `media.py sheet` and look at it. Check:
   - no layout character is visible, only capsules
   - capsules appear and vanish with their characters
   - cuts happen where the shots change
   - props are visible when `pipeline.props` is `show`

   Report the sheet path to the owner.

## 6. Write Archcore

Follow `../toon-setup/references/archcore-conventions.md`.

- **Scene log, Sequences table:** per sequence, the reference path, mode, `seconds`, `suggested_duration`, the .blend file name and its modified time, and the camera description of each shot.
- **Episode plan:** sequence and shot statuses set to `referenced`.

Finish with what was exported, the issues the owner should fix in Blender, and the next step, `toon-sequence`.
