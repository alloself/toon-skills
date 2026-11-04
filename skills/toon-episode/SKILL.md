---
name: toon-episode
description: >-
  Turn an episode script or outline into scenes and a shot list in an Archcore plan for the toon pipeline, and keep
  that plan in sync with the Blender markers once the episode is laid out. Shots get ids by the marker convention,
  durations, camera intent, cast and action text; scenes get empty logs. Does not touch Blender. Triggers:
  "plan the episode", "shot list", "break the script into scenes", "sync the plan with blender", "разбей сценарий",
  "план эпизода", "список шотов", "раскадровка эпизода", "сверь план с блендером".
metadata:
  author: alloself
  version: "0.1.0"
---

# toon-episode

The episode plan is the single table every other skill reads. It lists scenes, shots, sequences and decisions, each with a status. This skill writes it from the script, and later reconciles it with the layout.

## Before you start

1. Read `toon.yaml`. See `../toon-setup/references/passport.md`. If it is missing, send the owner to `toon-setup` and stop.
2. Find the episode number. Search Archcore for an existing plan `ep<NN>`, and update it instead of creating a second.
3. Talk in `series.language`.

## Mode A: script to plan

1. Get the script: a file, a pasted text or a spoken outline.
2. Split it into scenes. A new scene starts at a change of place or a jump in time. For each scene, record:
   - id, such as `S1`, following `blender.marker_regex`
   - location key from the passport, adding new locations as open items
   - characters
   - story beat in one line
   - target seconds
3. Split each scene into shots. For each shot, record:
   - id `<scene>_<num>_<desc>`, with `desc` short and filename-safe
   - seconds, rounded to 0.1. Half a second is a usable minimum, because sequences remove the 4 s per-shot limit
   - camera intent: size, angle and move, for example "close-up, low angle, slow push in"
   - characters in frame
   - action and acting: what happens, the emotion, turns, eyeline and props in hands. Mark the source `owner` when the owner wrote it
4. Show the scene table and then one scene's shots at a time. The owner edits in words; apply the edits and show the changes.
5. Mark open questions, such as who holds the lantern or where the owl enters. Suggest `toon-grill` for scenes that have many.

## Mode B: sync with Blender

Use when the episode is laid out or the layout changed.

1. Run `shots` with `camera=True` and `cast=True`. See `../toon-setup/references/blender-conventions.md`.
2. Compare with the plan:
   - shots in Blender but not in the plan
   - shots in the plan but not in Blender
   - durations that differ by more than 0.2 s
   - cast differences
   - camera moves that differ from the intent
3. Show the differences as one table. Ask which side wins, recommending Blender for timing and camera, and the plan for action and acting.
4. Apply the answers to the plan. Never change the .blend. Changes the layout needs go to the owner as a list.

## Write Archcore

Follow `../toon-setup/references/archcore-conventions.md`, with the template `../toon-setup/assets/archcore/episode.plan.md`.

- Create or update the plan `ep<NN>` in `episodes/ep<NN>` as `draft`, and add the relation `depends_on` to `series-bible`.
- New shots start at status `planned`. Sync mode sets laid-out shots to `laid-out`.
- Create an empty scene log `ep<NN>-<scene>-log` for every new scene, from `scene-log.doc.md`, linked to the plan with `implements`.
- When the owner approves the shot list, set the plan to `accepted`.

Finish with the scenes and shot counts, the open questions and the next step: `toon-grill` for unclear scenes, otherwise `toon-layout`.
