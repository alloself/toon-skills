# Project passport: toon.yaml

`toon.yaml` sits in the project root. It holds everything project-specific, so the skills stay generic. Template: `assets/toon.example.yaml`.

## Finding it

1. Look in the working directory, then in its parents, up to the filesystem root.
2. Not found: run `toon-setup`. Other skills stop and say so; they do not guess paths.
3. Paths in the passport are relative to the passport's folder unless absolute.

## Fields

| Field | Meaning | Default |
|---|---|---|
| `series.title` | Series name, used in doc titles and Higgsfield folder names | required |
| `series.language` | Language of chat and of every Archcore doc body | `en` |
| `series.style` | One style paragraph added to every generation prompt | required |
| `series.aspect`, `series.fps` | Output aspect ratio and frame rate | `16:9`, `24` |
| `characters[]` | `key`, `name`, `blender` root object, `prompt`, `sheet` (`file`, `media`, `doc`). List order fixes each character's capsule colour for the whole series | empty |
| `locations[]` | `key`, `name`, `prompt`, `plate` (`file`, `media`, `doc`) | empty |
| `blender.file` | Working .blend. Skills read it and never save it | required |
| `blender.access.kind` | `mcp`: a Blender MCP runs Python in a live Blender. `headless`: run `blender -b` from the shell | `mcp` |
| `blender.access.tool` | Name of the MCP tool that runs Python | `execute_blender_code` |
| `blender.access.exe` | Blender executable for `headless` | `blender` on PATH |
| `blender.char_prefix`, `char_names` | Character roots: top-level objects with the prefix, plus any listed names | `CHR_`, none |
| `blender.prop_prefix`, `prop_names` | Props characters hold, carry or push | `PRP_`, none |
| `blender.camera_prefix` | Shot cameras start with it (a hint only) | `CAM_` |
| `blender.seq_prefix` | A marker without a camera with this prefix forces a new sequence | `SEQ_` |
| `blender.marker_regex` | Parses shot markers into `scene`, `num`, `desc` | see example |
| `blender.exchange_dir` | Reference output folder as Blender sees it | `render/toon` |
| `blender.exchange_dir_local` | The same folder as the agent sees it, when Blender runs on another machine | same as above |
| `higgsfield.video_model`, `video_mode` | Model id and mode for sequences | `seedance_2_5`, `omni_reference` |
| `higgsfield.draft` | Generate drafts first, finalize approved drafts | `true` |
| `higgsfield.resolution_draft`, `_final` | Draft resolution when draft mode is unavailable; final resolution | `480p`, `1080p` |
| `higgsfield.generate_audio` | Native audio in generations | `false` |
| `higgsfield.image_model` | Only for missing sheets and plates | `nano_banana_pro` |
| `higgsfield.folder` | Higgsfield folder id for the series | none |
| `archcore.root`, `archcore.language` | Project root that holds `.archcore/`, doc language | `.`, series language |
| `output.*` | Local folders for bible images, references, takes and cuts | `bible`, `render/toon`, `takes`, `cuts` |
| `budget.confirm_per` | One approval covers a `scene` or one named `batch` | `scene` |
| `budget.max_retries` | Regenerations per sequence inside an approved batch | `2` |
| `budget.min_balance` | Warn when the balance after a batch drops below it | `50` |
| `pipeline.reference_mode` | What replaces characters in the Blender reference video, see `reference-modes.md` | `capsule` |
| `pipeline.props` | `show` keeps props visible in the reference; `hide` removes them | `show` |
| `pipeline.sequence_target` | Preferred sequence length in seconds | `[8, 15]` |
| `pipeline.sequence_max`, `sequence_min` | Longest and shortest generation | `30`, `4` |
| `pipeline.min_shot_seconds` | The file check warns about shots shorter than this | `0.5` |
| `pipeline.jump_m` | Continuity check: allowed root jump between shots of one scene, metres | `0.3` |

## Passing passport values to Blender

Every `toon_blender` command accepts the Blender settings as keyword arguments: `char_prefix`, `prop_prefix`, `camera_prefix`, `seq_prefix`, `char_names`, `prop_names`, `marker_regex`, `jump_m`, `aspect`, and `char_order`. Pass `char_order` as the list of `characters[].blender` names in passport order, so capsule colours stay the same in every sequence. Map `pipeline.sequence_max` to `max_shot_seconds` for `check`.

## Rules

- Change the passport only through a toon skill or with the owner's words. When the change is a decision (model, reference mode, style), record why in the matching Archcore doc.
- Media ids from Higgsfield go into `sheet.media` and `plate.media` as soon as the owner accepts a card.
- Never put credentials in the passport.
