---
name: toon-bible
description: >-
  Import, check and register character sheets and location plates for the toon pipeline. They are the only source of
  how characters and places look, because Seedance draws from them instead of from keyframes. Imports existing files or
  Higgsfield generations, checks the views (front, three-quarter, profile, back), uploads to Higgsfield, records media
  ids in toon.yaml and writes Archcore character and location cards. Generates a missing sheet or plate only when
  asked, after a cost estimate. Triggers: "add a character", "import character sheet", "location plate",
  "series bible", "карточка персонажа", "добавь персонажа", "фон локации", "плата локации", "библия сериала".
metadata:
  author: alloself
  version: "0.1.0"
---

# toon-bible

Seedance 2.5 knows how a character looks from every side only through its sheet, so it can turn, run and change pose freely. Each sheet is made once per series and reused in every generation. Plates do the same for locations.

## Before you start

1. Read `toon.yaml`. See `../toon-setup/references/passport.md`. If it is missing, tell the owner to run `toon-setup` and stop.
2. Shared references live in `../toon-setup/references/`. If that folder is missing, toon-setup is not installed: say so and stop.
3. Talk in `series.language`. Ask one question at a time, with a recommended answer.

## 1. What is needed

List the passport's characters and locations with their state: file present, `media` id present, Archcore card status. Ask which ones to work on; recommend those used in the next episode.

## 2. Find the source

For each item, in this order:

1. A path the owner gives, or a file already at `sheet.file` or `plate.file`.
2. The `output.bible` folder.
3. Higgsfield: `show_generations` with type image. Show the most recent few and let the owner pick.

When nothing exists, offer generation in step 5. Do not generate without being asked.

## 3. Check it

Look at every image yourself. Apply `references/card-checks.md` and report what passes, what fails and why. For each failure, offer three ways forward:
- use it as is
- generate a fixed version, which is paid
- the owner supplies another

Recommend one. Shots need the views a sheet is missing: a character without a back view will not turn away convincingly.

## 4. Register it

1. Copy or download the file to `sheet.file` or `plate.file` in the passport.
2. Upload it to Higgsfield and record the returned id in `sheet.media` or `plate.media`.
   - Use `media_upload` for a local file, or `media_import_url` for a URL.
   - Read the tool schema first, because these shapes are not verified yet. See `../toon-setup/references/higgsfield-cheatsheet.md`.
   - If a Higgsfield generation was picked, its media id may already be enough. Check the schema.
3. If Higgsfield offers saved characters through `manage_reference_elements` or `show_characters`, mention it to the owner. Do not switch to it without a decision recorded in an ADR.

## 5. Generate a missing card, only on request

1. Build the prompt from `references/card-checks.md` using the passport `prompt` and `series.style`. Use `higgsfield.image_model`.
2. Price it: `get_cost` for the number of variants, usually 2. Show the cost and the balance, and wait for a yes.
3. Generate, wait with `jobs_wait`, download with `../toon-setup/scripts/media.py fetch`, and show the variants.
4. The owner picks one, or asks for one fix within `budget.max_retries`. Then continue with steps 3 and 4.
5. Log the cost in the character or location card.

## 6. Write Archcore

Follow `../toon-setup/references/archcore-conventions.md`, with the templates `../toon-setup/assets/archcore/character.doc.md` and `location.doc.md`.

- Create or update `character-<key>` or `location-<key>` as `draft`: file, media id, views present, prompt, Blender root, capsule colour, and acting and props notes if the owner gave any.
- When the owner accepts the card, set it to `accepted`.
- Update the index in `series-bible`.

## 7. Report

Report the cards that are ready, the cards still missing and what each costs to generate. The next step is usually `toon-episode`, or `toon-layout` if the episode is already laid out.
