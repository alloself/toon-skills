<!-- create_document type=guide, filename=pipeline, directory=series. Steps are imperative, one action each, 20 words or fewer. -->
## Prerequisites

- MCP servers: archcore, higgsfield (authenticated), and a Blender MCP that runs Python or a headless Blender.
- ffmpeg and ffprobe on PATH.
- toon.yaml in the project root.
- Blender access: <mcp via tool X | headless with exe Y>. Exchange folder: <path as Blender sees it> is <path as the agent sees it>.
- Models: video <model, mode>; images <model>, used for cards only.

## Steps

1. Run toon-bible to import or create every character card and location plate.
2. Run toon-episode to turn the script into scenes and shots.
3. Run toon-grill on each scene before layout.
4. Lay out the scene in Blender with bound camera markers and named characters and props.
5. Run toon-layout to check the file, agree sequences and export capsule references.
6. Run toon-sequence to price the scene, get one approval and generate drafts.
7. Run toon-review on every draft, then finalize approved drafts with toon-sequence.
8. Run toon-assemble to cut the scene.

## Verification

- Every sequence in the scene log has a reference, a take, a verdict and its credits.
- The episode plan shows every shot as final or cut.

## Common Issues

<Filled in as they happen: symptom, cause, fix.>

### Tool facts

<What the live Higgsfield schema said: medias shape, upload method, draft parameters, reference limits, how prompts name references. Date each entry.>
