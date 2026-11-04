# Card checks and generation prompts

## Character sheet checks

| Check | Pass when |
|---|---|
| Views | Front, three-quarter, profile and back of the same character on one image. Four views fit in one reference slot |
| One character | Nobody else on the sheet |
| Pose | Neutral standing pose with arms slightly away from the body, so hands are readable |
| Background | Flat and plain, with no scenery |
| Model consistency | Same proportions, colours and details in every view |
| Signature items | Items the character always carries are shown, held the way they are held in the series |
| Style | Matches `series.style`: line, shading and palette |
| Text | No labels or captions on the figure. A small name tag in a corner is acceptable |
| Size | Long side at least 1024 px |

Optional extras, each as its own image only when a scene needs it: a face sheet with key expressions, and a close-up of the hands on a key prop. Reference slots per call are limited, so add extras per sequence, not per character.

## Location plate checks

| Check | Pass when |
|---|---|
| Empty | No characters |
| View | A wide establishing view showing the landmarks the scenes use |
| Match to layout | Landmarks sit roughly where the Blender set has them, such as the stream left to right and the hut on the far bank |
| Light | Time of day and season as the scenes need. Make a second plate when they change |
| Style | Matches `series.style` |
| Size | Long side at least 1280 px, aspect as `series.aspect` |

## Prompts for missing cards

Write image prompts in English, whatever the project language.

Character sheet:

```
Character turnaround sheet of <name>: <characters[].prompt>.
Four full-body views side by side on a plain light background: front, three-quarter, profile facing left, back.
Same character, same proportions and colours in every view, neutral standing pose, arms slightly away from the body,
<signature items and how they are held>.
<series.style>. No text, no other characters, no scenery.
```

Location plate:

```
Wide establishing view of <name>: <locations[].prompt>. <time of day, season, light>.
No people or characters. Clear landmarks: <list from the Blender set>.
<series.style>. Aspect <series.aspect>.
```

To fix a card rather than replace it, attach the old card as an image reference and say exactly what to change, for example: "Same character; add a back view; keep everything else."
