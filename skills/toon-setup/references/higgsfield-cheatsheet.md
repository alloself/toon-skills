# Higgsfield MCP cheatsheet

## Connect

```bash
claude mcp add --transport http higgsfield https://mcp.higgsfield.ai/mcp
```

Then run `/mcp` in Claude Code, pick `higgsfield` and authenticate in the browser. The server uses OAuth, so no key goes into any file. Without authentication every call returns 401.

## Tools

| Group | Tools |
|---|---|
| Generate | `generate_video`, `generate_video_batch`, `generate_image`, `generate_image_batch`, `motion_control`, `animation_actions`, `generate_3d` |
| Media | `media_upload`, `media_import_url`, `manage_reference_elements`, `show_characters`, `show_generations` |
| Info | `models_explore`, `get_workflow_instructions`, `get_presets`, `get_preferences`, `balance`, `transactions` |
| Jobs | `jobs_wait` |

Tool names and schemas can change. Before the first paid call in a session, read the live schema of every tool you will call. Where it disagrees with this page, the schema wins.

## Verified calls

These shapes come from real sessions.

```json
balance {}
models_explore {"action": "get", "model_id": "seedance_2_5"}
models_explore {"action": "recommend", "type": "video", "query": "multi-shot cartoon with references", "limit": 5}
show_generations {"type": "video", "only_completed": true, "size": 20}
transactions {"size": 20}
```

```json
generate_video {"params": {
  "model": "seedance_2_0", "prompt": "...", "aspect_ratio": "16:9", "duration": 5,
  "resolution": "1080p", "mode": "std", "generate_audio": false,
  "medias": [ ... ], "get_cost": true }}
```

- With `"get_cost": true`, nothing is generated and the reply is `{"cost": {"credits": N}}`. This is how every estimate is made.
- Without it, the reply is `{"results": [{"id": "<job id>", "status": "pending"}]}`.
- When the reply carries `notice.preset_recommendation`, the server suggests a preset that adds its own prompt and style. Do not accept it silently. Send the same call again with `"declined_preset_id": "<the notice's preset id>"`, unless the owner asked for presets.

```json
jobs_wait {"jobs": [{"index": 0, "job_id": "<id>"}], "timeout_seconds": 15}
```

Call `jobs_wait` in a loop until `all_terminal` is true. Each finished job has a `result_url`. Download it with `media.py fetch` right away, because result links can expire.

## Not yet verified

Read these from the live schema, `models_explore get` or `get_workflow_instructions` before the first generation. Record what you find in the pipeline guide. Do not guess.

| Item | What to look for |
|---|---|
| Shape of one `medias` item | Fields for the role and for the media id or URL. Roles seen: `start_image`, `end_image`, `image_references`, `video_references`, `audio_references` |
| How to upload local files | `media_upload` parameters, or `media_import_url` when the file is reachable by URL. Uploaded ids go into the passport |
| Draft flow for `seedance_2_5` | Exact names: seen as `draft` and `draft_job_id`. Check whether the final keeps the draft's motion during the pilot |
| Mode names for `seedance_2_5` | Seen: `t2v`, `omni_reference`, `video_edit`, `video_extension` |
| Reference limits | Maximum image references, video references and total reference-video seconds per call |
| How the prompt names a reference | For example "image 1" or `@Image1`. Without documentation, use plain words in upload order: "reference image 1 is Fox's character sheet" |
| Saved characters | Whether `manage_reference_elements` or `show_characters` can store a character so a call references it by id instead of re-sending the sheet |

## Models seen

| Model | Duration | Modes | Media roles |
|---|---|---|---|
| `seedance_2_5` | 4–30 s | `t2v`, `omni_reference`, `video_edit`, `video_extension`; draft and `draft_job_id`; 480p–1080p | all five |
| `seedance_2_0` | 4–15 s | `std`, `fast`; 480p–4k | all five |
| `kling3_0` | 3–15 s | `std`, `pro`, `4k` | start and end image only |
| `gemini_omni_flash_1_1` | 3–10 s | text, image, reference to video; edit | start, end, image and video references |
| `minimax_h3` | 4–15 s | not checked | not checked |

Prices seen for a 5 s clip at 9:16, November 2026:

| Model and settings | Credits |
|---|---|
| `seedance_2_0`, 1080p, std | 45 |
| `gemini_omni_flash_1_1`, 1080p | 22.5 |
| `kling3_0`, pro, sound off | 7.5 |
| `nano_banana_pro`, one image | about 2 |

`seedance_2_5` prices are not recorded yet. Always use `get_cost`.

## Spend gate

Every paid step follows these rules. The owner set them, so do not relax them on your own.

1. Build the whole batch first: every sequence of the scene, or the named batch.
2. Price each item with `get_cost`. Read `balance`.
3. Show one table, then wait for the owner's yes. A changed prompt after approval needs a new yes.

   | Sequence | Seconds | Mode | Pass | Credits |
   |---|---|---|---|---|

   Under it, give the total, the balance now and the balance after the batch. Then list each sequence's prompt.
4. Inside an approved batch, regenerate an item at most `budget.max_retries` times without asking again. Each retry is logged with its cost.
5. If the balance after the batch would fall below `budget.min_balance`, say so before asking.
6. Log every job: id, model, parameters, credits and result file in the scene log.
