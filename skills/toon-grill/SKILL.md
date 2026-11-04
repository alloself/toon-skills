---
name: toon-grill
description: >-
  Grill the owner about one scene of a cartoon before or during layout, so the shots hold together logically: story
  beat, who stands where at the start and the end, entrances and exits, eyelines, who holds what and when, timing per
  shot, what the camera must show, off-screen action, emotions and turns. One question at a time with a recommended
  answer, answering from the plan, cards and Blender wherever possible, until the shot list follows unambiguously.
  Writes decisions to the Archcore episode plan and the world state to the scene log. Triggers: "grill the scene",
  "check scene logic", "stress-test this scene", "допроси по сцене", "проверь логику сцены", "грильни сцену".
metadata:
  author: alloself
  version: "0.1.0"
---

# toon-grill

A scene that is unclear in words becomes a teleport, a floating prop or a frozen character on screen. This skill closes the gaps before layout and before credits are spent. The pattern follows Matt Pocock's `grill-me` skill: walk the decision tree, ask one question at a time, always give a recommended answer, and look things up instead of asking when you can.

## Before you start

1. Read `toon.yaml`. See `../toon-setup/references/passport.md`. If it is missing, send the owner to `toon-setup` and stop.
2. Read whatever exists, and do not ask what these already answer:
   - the episode plan (`ep<NN>`)
   - the scene log, including the previous scene's world state at its end
   - the character and location cards
   - the `continuity` rule
3. If the scene is already laid out, run `shots` with `scene`, `cast=True` and `camera=True`, and run `continuity`. See `../toon-setup/references/blender-conventions.md`. Positions, cameras and durations then come from the file.
4. Talk in `series.language`.

## How to ask

- One question per message. Use a question tool with options if the client has one.
- Put your recommended answer first, mark it as recommended and say why in one sentence.
- Make each question stand on its own: name the shot, the character and the prop.
- When an answer creates a new question, follow that branch before moving on.
- When an answer contradicts the plan, the cards, the layout or a continuity rule, say so and ask which one wins.

The order of the tree is in `references/question-tree.md`. Skip a branch that the files already settle, and state the answer you took from them.

## When to stop

Stop when every shot of the scene has:
- who is in frame, and where they start and end
- what each of them does and feels, including turns and eyelines
- who holds which prop, and when it changes hands
- what the camera must show, and roughly how long the shot runs

The world state at the scene's start and end must be known, and no rule must be broken without a reason the owner gave. If the owner stops early, record what is still open.

## Write it down

Follow `../toon-setup/references/archcore-conventions.md`.

| Where | What |
|---|---|
| Episode plan, Decisions | Each question, the answer and why, under the scene's heading |
| Episode plan, Shots | Action and acting per shot. Mark the acting source `owner` when the owner dictated the text, otherwise `skill` |
| Scene log | World state at scene start and planned world state at scene end |
| `continuity` rule | A new numbered clause, only when the owner states a rule that holds beyond this scene, such as "the broom never leaves Fox's hand indoors" |

Finish with a short summary of what was decided, what stays open and the next step: usually `toon-layout`, or `toon-episode` if the shot list itself changed.
