---
name: toon-setup
description: >-
  Set up a cartoon or animated-series project for the toon pipeline (Claude + Higgsfield Seedance + Blender + Archcore).
  Checks the MCP servers and ffmpeg, writes the toon.yaml project passport, scans the .blend for shots, characters,
  props and moving objects, and starts the Archcore docs: series bible, continuity rules, pipeline guide, research.
  Holds the shared scripts and references the other toon skills use. Use when starting a series or episode, on a new
  machine, or when another toon skill reports a missing passport. Triggers: "set up toon", "new series",
  "connect blender and higgsfield", "настрой проект мультфильма", "новый сериал", "подключи блендер и higgsfield",
  "создай паспорт проекта".
metadata:
  author: alloself
  version: "0.1.0"
---

# toon-setup

The first skill of the toon pipeline:

1. **Blender** fixes positions, scale, camera and cuts.
2. **Seedance 2.5** on Higgsfield draws the acting, from character sheets, location plates, a capsule reference video and a timed prompt.
3. **Archcore** keeps the series knowledge as you go.

This skill also holds what the other toon skills share:

| Path | What |
|---|---|
| `scripts/toon_blender.py` | Blender module: check, shots, continuity, sequences, export. See `references/blender-conventions.md` |
| `scripts/media.py` | ffmpeg helpers: probe, frames, sheet, compare, pad, fit, concat, fetch |
| `references/passport.md` | Every `toon.yaml` field |
| `references/archcore-conventions.md` | Which doc gets written when |
| `references/higgsfield-cheatsheet.md` | Tools, verified calls, spend gate |
| `references/reference-modes.md` | Capsule references and the pilot |
| `references/research.md`, `optional-paths.md` | Why the pipeline looks like this; routes outside v1 |
| `assets/toon.example.yaml`, `assets/archcore/*.md` | Passport and document templates |

Talk to the owner in `series.language` once it is known; before that, in the language they write in. Ask one question at a time, each with your recommended answer. Answer from files whenever you can instead of asking.

## 1. Find the project

- The project root is the working directory unless the owner names another.
- If `toon.yaml` exists, this is an update. Read it, show what is set and ask only about gaps or changes.

## 2. Check the tools

These checks are free. Run them and report one line per tool.

| Tool | Check | If missing |
|---|---|---|
| Archcore MCP | `list_documents` with `project` set to the root | Tell the owner to install the Archcore plugin, then continue without docs |
| Higgsfield MCP | `balance` | Give the commands from `references/higgsfield-cheatsheet.md` (`claude mcp add …`, then `/mcp` to authenticate). Continue; mark Higgsfield as pending |
| Blender | A Blender MCP with a Python tool: send `scripts/toon_blender.py` plus `print(TOON("install"))`, then call `version`. Otherwise run `blender --version`, or ask for the executable path | Ask how Blender is reached. Without Blender, stop after the passport |
| ffmpeg, ffprobe | `ffmpeg -version` | macOS: `brew install ffmpeg`. Windows: `winget install Gyan.FFmpeg` |
| Python 3.8+ | `python3 --version`, or `python` on Windows | Needed for `media.py` |

When Blender runs on another machine, test the exchange folder:
1. Through the Blender Python tool, write `_toon_probe.txt` into `blender.exchange_dir`.
2. Check that it appears in `blender.exchange_dir_local`.
3. Delete the probe file.

## 3. Read the layout

If a .blend is given, run `check` and `sequences` with the default settings. See `references/blender-conventions.md` for how to call them. Use the results to propose passport values instead of asking:

- render size and fps, which give `series.aspect` and `series.fps`
- the character roots found
- shot naming, and the share of markers that match `marker_regex`
- travellers: objects that move during shots but are neither characters nor props

For the travellers, ask one question that lists them all. For each, recommend character, prop or scenery from its `looks_like` hint. Characters go to `blender.char_names` and props to `blender.prop_names`. Renaming objects in the .blend is the owner's choice; the passport lists work without renaming.

## 4. Write the passport

Ask only what the files cannot tell, one question at a time:

1. Series title and language.
2. Style paragraph: one paragraph the owner agrees with, added to every prompt.
3. Characters: key, display name, Blender root and a one-line look. Their order fixes capsule colours for the whole series.
4. Locations: key, name and a one-line look.
5. Blender access: MCP tool name or headless executable, plus the exchange folders.
6. Budget: keep the defaults unless the owner changes them.

Fill `assets/toon.example.yaml`, write `toon.yaml` in the root, and show the owner the result. On an update, show only what changed.

## 5. Start Archcore

1. Ask once: "Initialize Archcore in `<root>` with language `<lang>`?" On yes, call `init_project` with that language. Skip this if `.archcore/` exists.
2. Create these docs as `draft`, from the templates in `assets/archcore/` and following `references/archcore-conventions.md`. Search first, and update instead of duplicating.

   | Doc | Content |
   |---|---|
   | `series-bible` (doc, `series`) | Premise if known, style paragraph, character and location index with capsule colours |
   | `continuity` (rule, `series`) | The six base rules from the template |
   | `pipeline` (guide, `series`) | Tools, access kind, folders and models from the passport, plus the results of step 2 |
   | `pipeline-approach` (rnd, `series/research`) | Findings from `references/research.md` |
   | `source-<name>` (evidence, `series/research`) | One per source in `references/research.md`, linked to the rnd with `supports` |

3. On a re-run, update these docs instead of recreating them.

## 6. Report

End with a short summary in the owner's language:
- what is ready
- what is pending, such as Higgsfield authentication, missing cards or layout errors
- what to run next: usually `toon-bible`, then `toon-episode`

Never put credentials into `toon.yaml` or Archcore.
