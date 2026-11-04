# Sequence prompts

Write the prompt in English. Keep the order below, because the model reads it top-down.

## Template

```
<series.style>

References:
- Image 1 is <Fox>'s character sheet (front, three-quarter, profile, back).
- Image 2 is <Owl>'s character sheet.
- Image 3 is the <forest glade> location.
- [Image 4 shows how the previous scene moment ended: <one line of state>. Continue from that state.]
- Video 1 is the layout. Follow its camera moves, cuts, framing and timing exactly.
  The coloured capsules in Video 1 are placeholders, never draw them:
  red capsule = <Fox>, blue capsule = <Owl>.
  Keep each character where its capsule is, on the same path, at the same size in frame.
  Draw the characters from their sheets. Invent natural acting from the text below.

Shot 1, 0.0-2.5 s. <camera description>. <acting>.
Cut. Shot 2, 2.5-5.0 s. <camera description>. <acting>.
...
Shot N, <t0>-<t1> s, holds until <duration> s. <camera description>. <acting>.

Only <Fox> and <Owl> appear. No text, no subtitles, no capsules, no mannequins.
Natural weight and timing: feet plant on the ground, no sliding, no stiff robotic moves.
```

How the prompt names references depends on the model; see Tool facts in the pipeline guide. Without documentation, use plain words in upload order, as above.

## Filling it from sequence.json

| Prompt part | Source |
|---|---|
| Shot times | `shots[].t0`, `shots[].t1`. The last shot holds until `suggested_duration` |
| Camera | `shots[].camera_move.description`, word for word |
| Colour legend | `legend[<character>].color` for every character in `in_frame` |
| Who is where | `shots[].cast.first` and `last`. Say it only when it helps: "Fox on the left third, Owl far right, small" |
| Props | `holds` and `near` in the cast, plus the plan's prop notes |
| Acting | the episode plan's Shots table: owner text word for word, or written by the skill |
| State | world state at the end of the previous sequence, from the scene log |

## Writing the acting

- **One main action per shot**, with a physical verb: grabs, drags, ducks, flinches, tiptoes.
- **Emotion through the body and face:** "shoulders up, eyes wide, mouth open". "Scared" alone says little.
- **Turns explicitly:** "turns her back to camera", "spins to face Owl". Without the words, characters keep facing one way.
- **Eyelines:** "looks at Owl", "looks off screen left at the noise".
- **Hands and props exactly:** which hand, which end, one or two hands, how heavy it is. For example: "grabs the plank with both hands at one end and drags it; the far end scrapes the grass".
- **Speech:** without generated audio, describe the mouth and the gesture, such as "talks fast, waving the ladle". Do not quote lines.
- **No camera words in the acting.** The camera is in the camera description and in Video 1.
- **Close-ups:** in a close-up the capsule fills the frame, so the text carries the whole picture. Say whose face it is, what the expression is and what the hands do.

## Example

```
2D storybook cartoon, soft cel shading, warm muted palette, thick clean outlines, painted forest backgrounds.

References:
- Image 1 is Fox's character sheet. Image 2 is Owl's character sheet. Image 3 is the forest glade.
- Video 1 is the layout. Follow its camera moves, cuts, framing and timing exactly.
  The coloured capsules in Video 1 are placeholders, never draw them: red capsule = Fox, blue capsule = Owl.
  Keep each character where its capsule is, on the same path, at the same size in frame.

Shot 1, 0.0-2.5 s. Eye-level full shot, wide lens. Locked-off camera. Fox drags a long wooden plank toward the
stream with both hands at one end, leaning back, tail stiff with effort; the far end scrapes the grass.
Cut. Shot 2, 2.5-3.5 s. Close-up, short telephoto lens. Fox's face, cheeks puffed, eyes squeezed shut, then one eye
opens to peek at the stream.
Cut. Shot 3, 3.5-6.0 s, holds until 7 s. High-angle medium shot. Camera slowly pushes in 1.2 m. Owl lands on the log
behind Fox, folds his wings, tilts his head and watches her, unimpressed.

Only Fox and Owl appear. No text, no subtitles, no capsules, no mannequins.
Natural weight and timing: feet plant on the ground, no sliding, no stiff robotic moves.
```

## Fixing a take

The review verdict names what to change. Change the smallest thing:

| Problem | Change |
|---|---|
| Wrong action | the acting line of that shot |
| Character off model | make the sheet reference explicit in that shot: "Fox exactly as in image 1" |
| Capsule leaked | strengthen the placeholder line, and name the capsule colour that leaked |
| Camera ignored | repeat the camera description, then add "camera exactly as in Video 1" |

If two retries do not fix the camera, positions or cuts, the problem is in the layout: the verdict is relayout. If two retries do not fix the acting, ask the owner for the acting text.
