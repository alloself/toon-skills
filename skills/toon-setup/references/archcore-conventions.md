# Archcore conventions

Archcore keeps the series knowledge in `.archcore/` as Markdown: `<slug>.<type>.md`. The toon skills write it as they go, so the bible, the plans and every generation are documented without the owner asking.

## Rules for every skill

1. Write through the Archcore MCP tools only: `list_documents`, `search_documents`, `get_document`, `create_document`, `update_document`, `add_relation`.
2. Search before creating, and update the existing doc instead of making a second one.
3. Create docs as `draft`. Set `accepted` only after the owner confirms in words, for example by accepting a card, approving a shot list or picking the pilot winner.
4. Write after each completed step, without asking. A step is complete when its files exist and its result is known.
5. Headings come from the templates in `toon-setup/assets/archcore/` and stay in English. Bodies are written in `archcore.language`.
6. Never ask to remove a doc as part of normal work. A removal needs the owner's explicit request.
7. `init_project` runs only in `toon-setup`, after the owner agrees, with `language` set to `archcore.language`.

## Documents

| Doc | Type | Slug | Directory | Written by |
|---|---|---|---|---|
| Series bible: premise, tone, style paragraph, character and location index | `doc` | `series-bible` | `series` | setup, bible |
| Character card | `doc` | `character-<key>` | `series/characters` | bible |
| Location card | `doc` | `location-<key>` | `series/locations` | bible |
| Continuity rules | `rule` | `continuity` | `series` | setup; grill and review add rules |
| How this project runs the pipeline | `guide` | `pipeline` | `series` | setup; updated when tools or settings change |
| Pipeline decisions, such as the reference mode or the model | `adr` | `pipeline-<topic>` | `series` | review, and any skill after an owner decision |
| Pipeline research | `rnd` | `pipeline-approach` | `series/research` | setup |
| One external source | `evidence` | `source-<short-name>` | `series/research` | setup |
| Episode plan: scenes, shots, sequences, decisions | `plan` | `ep<NN>` | `episodes/ep<NN>` | episode, grill, layout, review |
| Scene log: sequences, takes, spend, world state | `doc` | `ep<NN>-<scene>-log` | `episodes/ep<NN>` | layout, sequence, review, assemble |

Slugs are lowercase with hyphens: scene `S10` becomes `s10`, so the log for episode 1 scene S10 is `ep01-s10-log`.

## Relations

Add a relation only when both documents justify it.

| From | To | Type |
|---|---|---|
| `evidence` source | `pipeline-approach` rnd | `supports` |
| `pipeline-reference-mode` adr | `pipeline-approach` rnd | `depends_on` |
| Episode plan | `series-bible` | `depends_on` |
| Scene log | episode plan | `implements` |
| Newer adr | older adr on the same topic | `supersedes` |

## What gets written when

| Step done | Update |
|---|---|
| Passport written | Pipeline guide: tools, models, access kind, folders |
| Card imported or accepted | Character or location card: files, media id, prompt, views present; bible index |
| Scene grilled | Episode plan, Decisions section; scene log, world state at scene start; new continuity rules |
| Shot list built | Episode plan, Shots table, all at `planned` |
| Layout checked | Episode plan, issues found; continuity findings in the scene log |
| Sequences agreed | Episode plan, Sequences table; scene log, Sequences table |
| References exported | Scene log: reference files, mode, .blend version, camera descriptions |
| Batch approved | Scene log, Spend: estimate, balance, the owner's approval |
| Take downloaded | Scene log, Takes: job id, model, parameters, credits, file |
| Take reviewed | Scene log verdict; episode plan statuses; continuity rules if a new rule came up |
| Pilot decided | `pipeline-reference-mode` adr; pipeline guide; passport `pipeline.reference_mode` |
| Scene assembled | Scene log: cut file, world state at scene end; episode plan statuses |

## Statuses in the episode plan

Shots and sequences move through `planned`, `laid-out`, `referenced`, `drafted`, `approved`, `final` and `cut`. A sequence that needs a new layout goes back to `laid-out`.

## Line formats

Takes table in the scene log:

| Sequence | Pass | Job | Model | Mode | Seconds | Credits | File | Verdict |
|---|---|---|---|---|---|---|---|---|
| S10_B | draft 1 | `<job id>` | seedance_2_5 | capsule | 10 | `<n>` | takes/S10/S10_B_d1.mp4 | regenerate: Owl holds the plank with one hand |

The world state lists, per character: where they are, what they hold, what changed, such as clothes, injuries or mood. It also lists the state of props and of the set, such as "plank lies across the stream".
