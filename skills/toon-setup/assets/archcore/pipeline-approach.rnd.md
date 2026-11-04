<!-- create_document type=rnd, filename=pipeline-approach, directory=series/research. Each finding cites an evidence doc. -->
## Goal

Keep positions, scale, perspective and camera consistent from shot to shot, without passing Blender's stiff motion to the video model.

## Questions

1. Which inputs keep layout and camera but leave the acting free?
2. How do short shots fit a model with a 4-second minimum?
3. How do characters stay on model across shots without start frames?

## Approach

A survey of published workflows and model guides, then a pilot on one sequence of this series.

## Findings

<Copy the findings from toon-setup/references/research.md, each pointing to its evidence doc.>

## Recommendation

Blender exports one reference per sequence, with characters as coloured capsules. Seedance 2.5 generates several shots per call from character sheets, location plates, that reference and a timed prompt. There are no keyframes.

## Next Action

Run the pilot and record the result in pipeline-reference-mode.
