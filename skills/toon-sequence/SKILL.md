---
name: toon-sequence
description: >-
  Generate a cartoon scene with Seedance 2.5 on Higgsfield, one generation per sequence of shots. Builds a timed
  multi-shot prompt from the Blender capsule reference (camera, cuts, positions, colour legend), character sheets,
  location plates and the acting text; prices the whole batch, asks once, runs drafts, hands each take to review, and
  finalizes approved drafts. No keyframes and no start frames. Sticky sequences continue from the previous approved
  take. Triggers: "generate the scene", "generate sequence", "run seedance", "finalize the drafts",
  "сгенерируй сцену", "сгенерируй секвенцию", "запусти седанс", "финал по черновикам".
metadata:
  author: alloself
  version: "0.1.0"
---

# toon-sequence

One Seedance 2.5 call covers one sequence: several consecutive shots, 4 to 30 seconds, with cuts inside. Seedance gets:
- the character sheets and location plates as image references
- the Blender capsule render as a video reference, which carries camera, cuts and positions
- a prompt that walks through the shots with timecodes and says what everyone does

Seedance invents the acting. Blender decides where everything is.

## Before you start

1. Read `toon.yaml`. See `../toon-setup/references/passport.md`. If it is missing, send the owner to `toon-setup` and stop.
2. Read `../toon-setup/references/higgsfield-cheatsheet.md` and follow its spend gate exactly.
3. Preconditions. For anything missing, name the skill that fixes it and stop.
   - Every sequence to generate is `referenced` in the episode plan and has `sequence.json` and `ref_<mode>.mp4` (`toon-layout`).
   - Every character and location in frame has an accepted card with a `media` id (`toon-bible`).
   - The Higgsfield MCP answers `balance`.
4. Talk in `series.language`. Write prompts in English.

## 1. Session check

This step is free.
1. Call `balance`, then `models_explore` with `action: get` for `higgsfield.video_model`.
2. Read the live schema of `generate_video` and of the upload tool.
3. Note the facts that matter: modes, duration range, resolutions, the draft parameters, the shape of a `medias` item, the reference limits, and how the prompt names references.
4. When they differ from the cheatsheet or the pipeline guide, record them under Tool facts in the `pipeline` guide.

## 2. Prepare the inputs

For every sequence of the batch:

1. Pad the reference to the generation length:
   `media.py pad ref_<mode>.mp4 ref_<mode>_gen.mp4 --seconds <suggested_duration>`.
   Keep `suggested_duration` within the model's duration range.
2. Upload the padded reference and record its id in the scene log. Sheets and plates already have ids in the passport.
3. For a sticky sequence, the state image comes later. See step 6.
4. Count the references. If the sequence needs more than the model allows, drop the least important plate first, then ask.

## 3. Build the prompts

Follow `references/sequence-prompts.md`. Per shot, the camera comes from `shots[].camera_move.description`, and positions come from the cast boxes. The acting comes from the episode plan:
- If the acting source is `owner`, use the text word for word.
- If it is `skill`, write it from the plan, the grill decisions and the character cards.

Version every prompt (v1, v2 …) and store it in the scene log.

## 4. Price and ask once

1. For each sequence, call `generate_video` with the full parameters and `get_cost: true`. Use draft mode when `higgsfield.draft` is true and the model supports it. Otherwise use `higgsfield.resolution_draft`.
2. Show one message:
   - the table from the spend gate: sequence, seconds, mode, pass and credits
   - the total, the balance now and the balance after
   - a warning when the balance after drops below `budget.min_balance`
   - every prompt, each labelled with its sequence
3. Wait for the owner's yes. If the owner edits a prompt or gives their own acting text, apply it and set that shot's acting source to `owner` in the plan. Re-price only if the parameters changed. A changed batch needs a new yes.
4. Log the estimate, the balance and the approval in the scene log, under Spend.

## 5. Generate drafts

1. Submit every non-sticky sequence. Use `generate_video_batch` if the schema supports these inputs, otherwise one call each.
2. If a reply carries `notice.preset_recommendation`, resend with `declined_preset_id`.
3. Loop `jobs_wait` until all jobs are terminal. Download each result with `media.py fetch` to `<output.takes>/<scene>/<sequence>_d<N>.mp4`.
4. Log every take: job id, model, mode, parameters, credits and file.
5. Run `toon-review` on each take as it lands.
   - **regenerate:** apply its prompt changes as a new prompt version and generate again. Stay within `budget.max_retries` per sequence without asking. Past that, ask the owner.
   - **relayout:** stop that sequence and send it back to `toon-layout`, with status `laid-out`.

## 6. Sticky sequences

A sticky sequence starts only after the sequence before it is approved.
1. Grab the approved take's last frame with `media.py frames <take> <dir> --at last`.
2. Upload it and add it as one more image reference, described in the prompt as the state at the start, not as a start frame.
3. Generate it as in step 5. It is part of the same approved batch; its cost was in the estimate.

## 7. Finalize

1. When the owner approves the drafts of a scene, price the finals with `get_cost`.
   - In draft mode, use the approved draft's job id as `draft_job_id`.
   - Otherwise, use the same prompt and inputs at `higgsfield.resolution_final`.
2. Show the cost and ask once for the scene. Generate, download to `<sequence>_f<N>.mp4`, and log.
3. Review each final quickly against its draft. If a final changes the motion noticeably, report it. The pilot ADR records whether draft-to-final keeps motion.

## 8. Write Archcore

Follow `../toon-setup/references/archcore-conventions.md`.

| Doc | What changes |
|---|---|
| Scene log | Prompts, Takes and Spend tables updated as each step completes |
| Episode plan | Sequence statuses `drafted`, then `approved`, then `final` |

Finish with the takes made, the credits spent, the balance left, any open regenerations and the next step: review or `toon-assemble`.
