<!-- create_document type=rule, filename=continuity, directory=series. One requirement per numbered clause, active voice, one modal, 25 words or fewer. -->
## Rule

1. WHEN a shot cuts to the next shot of the same scene, the layout MUST keep every character root within jump_m of its previous position.
2. IF a character jumps further across a cut, THEN the episode plan MUST state the reason, such as a time skip.
3. The Blender layout MUST be the only source of positions, scale and camera for every sequence.
4. WHEN a character holds a prop at the end of a sequence, the next sequence prompt MUST state who holds it and how.
5. WHEN a boundary cuts through one continuous action, the next sequence MUST use the approved previous take's last frame as a state reference.
6. The toon-sequence skill MUST NOT send start frames or restyled keyframes to the video model.

## Rationale

Characters that teleport between cuts break the film. Blender fixes space, and the video model invents the acting. Props in hands are where models fail most, so the text spells them out.

## Examples

### Good

<Shot 12 starts with the fox where shot 11 left her, still holding the plank.>

### Bad

<Shot 12 starts 3 m away with empty hands, and nothing in the plan explains it.>

## Enforcement

toon-layout runs the continuity check before every export. toon-review checks positions, props and character count in every take.
