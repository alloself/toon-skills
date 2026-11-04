# Blender conventions and the toon_blender module

Blender is the plan of the film, not its animation. It fixes where everyone stands, how big they are in frame, what the camera does and where the cuts are. Seedance draws the acting. Everything here serves that split.

## Scene convention

| Thing | Convention | Passport override |
|---|---|---|
| Shot | A timeline marker with a bound camera. It runs until the next camera marker; the last one runs to the scene end | none |
| Shot name | `<scene>_<num>_<desc>`, e.g. `S5_18_fox_backs_away` | `blender.marker_regex` |
| Character | A root object named with the character prefix; everything under it belongs to the character | `char_prefix`, `char_names` |
| Prop | An object a character holds, carries or pushes. A child of the character counts as held; a loose prop near the character is listed as `near` | `prop_prefix`, `prop_names` |
| Sequence break | A marker without a camera whose name starts with the sequence prefix | `seq_prefix` |
| Note | Any other marker without a camera | none |

To bind a camera, select it, put the playhead on the marker and choose Marker > Bind Camera to Markers. One .blend per episode is the usual layout.

The skills never save the working file and never edit the scene unless the owner asks. Exports render in a separate background Blender from the saved file. When the open file is unsaved or has unsaved changes, the export writes a copy first and renders that.

## Calling the module

The module is one file: `toon-setup/scripts/toon_blender.py`. Every command returns JSON.

### Through a Blender MCP (`blender.access.kind: mcp`)

1. Once per machine, and again after updating the skills, read the whole file and send it through the MCP Python tool, followed by:

   ```python
   print(TOON("install"))
   ```

   This installs `toon_blender_core` into Blender's user scripts modules, which Blender puts on its import path at every start.

   When Blender runs on the same machine as the agent, or can see the skills folder, skip sending the text and exec the file by path:

   ```python
   p = r"<toon-setup>/scripts/toon_blender.py"; exec(compile(open(p, encoding="utf-8").read(), p, "exec")); print(TOON("install"))
   ```
2. Every later call is short. Pass the passport's Blender settings each time:

   ```python
   import importlib, toon_blender_core as T; importlib.reload(T)
   print(T.TOON("check", char_prefix="CHR_", char_names=["BEAVER_root"], aspect="16:9"))
   ```

3. Call `T.TOON("version")` first in a new session. If the import fails, or `version` differs from `VERSION` in the file you have, install again.
4. Through the MCP, `export` returns at once with a job folder and renders in a background Blender. Poll `TOON("status", job=...)` every 20 to 30 seconds. Never block the MCP with a long render.

### Headless (`blender.access.kind: headless`)

```bash
blender -b ep01.blend --python toon_blender.py -- toon '{"cmd": "check"}'
blender -b ep01.blend --python toon_blender.py -- toon @calls.json
```

- The result is printed between `<<<TOON` and `TOON>>>` as ASCII-escaped JSON.
- With the environment variable `TOON_RESULT=<path>`, the same result is also written there as UTF-8. Prefer this when names are not in English.
- A JSON list runs several calls in one Blender start. Batch calls, because loading a big .blend is the slow part.
- Headless `export` renders inline and returns when done.
- On Windows, pass native paths (`C:\...`) to Blender. Put non-ASCII arguments in an `@file` written as UTF-8.

## Commands

| Command | Arguments | Returns |
|---|---|---|
| `version` | none | module and Blender versions, file, background flag |
| `install` | none | installed path, next call to use |
| `check` | `aspect`, `max_shot_seconds`, `min_shot_seconds`, prefixes and name lists | `errors`, `warnings`, `info`, shot and character counts, `ok` |
| `shots` | `scene`, `ids`, `cast=True`, `camera=True` | per shot: id, scene, frames, seconds, camera; optionally cast at first and last frame and `camera_move` |
| `continuity` | `scene`, `inside=True`, `step`, `cut_m` | root jumps between consecutive shots of one scene, teleports inside shots |
| `sequences` | `scene`, `target=[8, 15]`, `max_seconds=30`, `min_seconds=4` | proposed sequences with shots, seconds, cast, why each ends, `boundary`, `sticky_next_suggested`, warnings |
| `export` | `sequences=[{id, shots}]` or `shots=[ids]`, `modes=["capsule"]`, `out`, `ref_scale=100`, `props="show"`, `stills=False`, `engine` | job folder and state |
| `status` | `job` | `state` (queued, running, done, error), done files, errors, current item |

Every command also accepts `char_prefix`, `prop_prefix`, `camera_prefix`, `seq_prefix`, `char_names`, `prop_names`, `char_order`, `marker_regex` and `jump_m`.

### What `check` reports

- **Errors:** no camera markers, duplicate shot names, no characters.
- **Warnings:**
  - marker names that do not parse, and shots outside the length limits
  - a render aspect that differs from the passport
  - travellers: objects that move during shots but are neither characters nor props
- **Info:** sequence-break markers, note markers, cameras without the prefix.

Travellers matter most. A moving rig that is not marked as a character keeps its mannequin in the reference, and Seedance copies its robotic motion. A carried object that is not marked as a prop is missing from the prompt. For each traveller, ask the owner which one it is, then add it to `char_names` or `prop_names`, or leave it as scenery. Renaming objects in the .blend is the owner's call.

### How `sequences` cuts

Shots of one scene are taken in order. A new sequence starts at the first of these that applies:

1. A sequence-break marker sits between the shots.
2. The next shot would push the sequence past `max_seconds`.
3. A character root jumps more than 1 m across the cut, or more than three times `jump_m` if that is larger. Applies once the sequence is at least `min_seconds` long.
4. A new character comes into frame. Applies once the sequence is at least the lower target.
5. The upper target is reached, or the next shot would pass it once the lower target is met.

A last piece shorter than `min_seconds` is merged into the previous sequence when it fits. Cuts of type `length` may split an action: ask the owner whether the next sequence is sticky.

## Export output

```
<out>/
  _job.json  _status.json  _worker.log  _toon_worker.py  [_source.blend]
  <sequence>/
    sequence.json
    ref_capsule.mp4          one file per mode
    stills/<shot>.png        only with stills=True: first frame of each shot, characters as they are
```

`sequence.json` holds:

| Field | Meaning |
|---|---|
| `sequence`, `scene` | ids |
| `frame_start`, `frame_end`, `frames`, `seconds`, `fps` | exact length of the sequence |
| `suggested_duration` | whole seconds to generate: `seconds` rounded up, at least 4 |
| `legend` | per character: capsule `color` name and `rgb`; stable across the series when `char_order` is passed |
| `in_frame` | characters in frame at the first or last frame of any shot |
| `shots[]` | per shot: id, `t0` and `t1` in seconds from the sequence start, `camera_move`, cast at first and last frame |
| `camera_move` | `description` in words plus `moves`, `static`, `drift`, `shot_size`, `angle`, lens, start and end pose |
| cast entry | `in_frame`, `box` (left, top, right, bottom as frame fractions), `height_frac`, `world`, `distance_m`, `holds`, `near` |
| `props`, `modes`, `files`, `blend`, `created` | how it was made |

The camera `description` is meant to go straight into the prompt, for example: "Eye-level medium shot, wide lens (30 mm equiv.). Camera quickly pulls back 7.9 m over 5.0 s."

## Timing

- The reference covers exactly `seconds`. The generation covers `suggested_duration`, which is never shorter.
- Before upload, hold the last frame of the reference until `suggested_duration` with `media.py pad`. The prompt says the last shot holds to the end.
- `toon-assemble` trims each take back to `seconds`.

## Blender on another machine

Blender writes to `blender.exchange_dir` as Blender sees it. The agent reads the same files from `blender.exchange_dir_local`. A shared folder is needed, such as an SMB share, Syncthing or a cloud drive. When the agent cannot see the files, it says so and stops; it never retries the render.

## Safety

- Never call `save_mainfile` on the working file. The only save is `save_as_mainfile(copy=True)` into the job folder.
- Never change the scene to make an export work. Report the problem and the fix to the owner.
- Renders run in a separate process. Closing Blender does not stop a running job; `status` shows its state.
