# toon-skills

[Русская версия](README.ru.md)

Agent skills for making a consistent cartoon series with **Claude Code**, **Higgsfield Seedance 2.5**, **Blender** and **Archcore**.

- **Blender plans the shots:** where everyone stands, how big they are, what the camera does, where the cuts are.
- **Seedance draws the acting:** from character sheets, location plates and a timed prompt.
- **Archcore documents the series as you work.**

## Why

Using a Blender layout video as a Seedance reference has a cost: the model copies the mannequins' motion. Characters slide, move like robots and hold props badly. Dropping Blender loses the plan instead: characters teleport between cuts, and scale and perspective drift.

Restyled keyframes for every shot do not help either. A start frame freezes the first pose and the camera, so characters cannot turn and the camera cannot move. It also costs an image generation per shot, often several, and Seedance's 4-second minimum wastes credits on short shots.

These skills split the work:

| Source | Carries | Never carries |
|---|---|---|
| Blender reference video, with characters drawn as coloured **capsules** | camera moves, cuts, framing, positions, paths, scale, props | limbs, poses, acting |
| Character sheets and location plates, made once per series | how characters and places look from every side | positions |
| Timed prompt | who does what in each shot: emotion, turns, eyelines, grips | camera |

One Seedance 2.5 generation covers one **sequence**: several consecutive shots, 4 to 30 seconds, with the cuts inside. There are no keyframes and no start frames.

## Skills

| Skill | Does |
|---|---|
| `toon-setup` | Checks MCP servers and ffmpeg, writes the `toon.yaml` passport, scans the .blend, starts Archcore. Holds the shared scripts and references |
| `toon-bible` | Imports and checks character sheets and location plates, uploads them to Higgsfield, writes the cards. Generates missing ones only on request |
| `toon-episode` | Turns a script into scenes and a shot list, and keeps it in sync with Blender |
| `toon-grill` | Grills you about one scene, one question at a time, until the shots are logically sound |
| `toon-layout` | Checks the Blender layout, proposes sequences, exports capsule references with cuts and camera data |
| `toon-sequence` | Builds timed multi-shot prompts, prices the scene, asks once, runs drafts, then finalizes the approved ones |
| `toon-review` | Compares each take with its reference shot by shot and gives a verdict: approved, regenerate or relayout |
| `toon-assemble` | Trims takes to length and cuts the scene |

## Install

With the [skills CLI](https://github.com/vercel-labs/skills), into Claude Code for your user:

```bash
npx skills add alloself/toon-skills -g -a claude-code -s '*' -y
```

Or as a Claude Code plugin, which also registers the Higgsfield MCP server:

```
/plugin marketplace add alloself/toon-skills
/plugin install toon-skills@toon-skills
```

Update later with `npx skills update -g`, or through `/plugin`.

## Requirements

| Need | How |
|---|---|
| Claude Code | macOS, Windows or Linux |
| Archcore MCP | Install the Archcore plugin: https://github.com/archcore-ai/archcore |
| Higgsfield MCP | `claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp`, then `/mcp` to sign in. The plugin install adds it for you |
| Blender 4.2 or newer | Either a Blender MCP whose tool runs Python, such as `execute_blender_code`, or a `blender` executable for headless runs. Blender may run on another machine if both see one shared folder |
| ffmpeg, ffprobe, Python 3.8+ | macOS: `brew install ffmpeg` |

## Quick start

In your project folder:

1. `/toon-setup`: answer a few questions, and get `toon.yaml` and `.archcore/`.
2. `/toon-bible`: import your character sheets and location plates.
3. `/toon-episode`: paste the script and get scenes and shots.
4. `/toon-grill`: settle each scene's logic.
5. Lay the scene out in Blender. Use timeline markers named `S1_01_fox_enters` with bound cameras, characters as `CHR_*` roots and props as `PRP_*`. Other names can be listed in the passport.
6. `/toon-layout`: check the file, agree the sequences and export the references.
7. `/toon-sequence`: see the estimate and the prompts, say yes once, and get the drafts.
8. `/toon-review` runs on every take. Approve, then `/toon-sequence` finalizes.
9. `/toon-assemble`: get the scene cut.

The first sequence is a **pilot**. It is rendered with capsule and frozen references side by side, and the winner becomes the series default in an Archcore ADR.

## Credits

No paid call runs without your yes. Each scene gets one estimate: per-sequence credits, the total, and the balance before and after. Inside an approved batch, a sequence is retried at most twice without asking. Every job and its credits go to the scene log.

## Status

Version 0.1.0.

**Tested:** the Blender module, headless on Blender 5.1 with a real 207-shot episode. That covers the check, continuity, sequence proposals and capsule references with cuts. The ffmpeg helpers are tested too.

**Not yet verified:**
- The exact Higgsfield schemas for media upload, the shape of a `medias` item and the Seedance 2.5 draft parameters. The skills read the live schema before the first paid call.
- How Seedance 2.5 treats capsule references. The pilot answers this.

## Credits for ideas

- Grilling pattern: Matt Pocock's `grill-me` skill.
- Documentation as you go: Archcore skills.
- Research sources: `skills/toon-setup/references/research.md`.

## License

MIT
