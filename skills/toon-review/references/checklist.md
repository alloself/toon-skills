# Take checklist

Each item is pass, fail or not applicable. Note the time and shot of each failure.

## Plan: from the reference, blocking

| # | Check | How |
|---|---|---|
| 1 | **Camera:** same moves, direction and rough speed per shot | Compare rows; `camera_move.description` |
| 2 | **Cuts:** a cut within about 0.2 s of every `t1`, and no extra cuts | Frames after each cut |
| 3 | **Framing:** shot size and angle match | Compare rows |
| 4 | **Positions:** each character where its capsule is, left or right and near or far | Compare rows; cast boxes |
| 5 | **Scale:** relative heights as in the layout | Compare rows; `height_frac` |
| 6 | **Paths:** characters move where their capsules move, in the same direction | Contact sheet |
| 7 | **Count:** exactly the characters in `in_frame`, nobody extra, nobody missing | Every row |
| 8 | **Environment:** landmarks where the layout has them | Compare rows; location card |

## Characters: blocking

| # | Check | How |
|---|---|---|
| 9 | **On model:** shape, colours and signature items as on the sheet, from every side shown | Card next to frames |
| 10 | **Props:** the right character holds the right prop, in the hand and way the prompt says; no prop appears or vanishes | Rows; plan prop notes |
| 11 | **No leaks:** no capsule, mannequin or grey blockout shape drawn as an object | Every frame |
| 12 | **Continuity:** the start matches the previous sequence's end state; the end matches the planned end state | Scene log world state |

## Acting: not blocking alone, but two failures together trigger a regenerate

| # | Check | How |
|---|---|---|
| 13 | **Alive:** weight, anticipation and follow-through; not stiff | Contact sheet; extra frames |
| 14 | **No sliding:** feet plant when walking; no skating | Frames every 0.25 s |
| 15 | **Action:** each shot shows its main action from the prompt | Rows |
| 16 | **Emotion and eyeline:** readable, looking where the prompt says | Rows |
| 17 | **Turns:** a character turns when the prompt asks | Contact sheet |

## Technical

| # | Check | How |
|---|---|---|
| 18 | **Length and size:** duration and resolution as ordered | `media.py probe` |
| 19 | **Artifacts:** no flicker, melting, warped faces or text on screen | Contact sheet |

## Verdict rules

- Any failure in 1 to 8 that a prompt cannot fix gives `relayout`. A wrong path in the layout itself is one example.
- Failures in 1 to 8 that the prompt ignored, and any failure in 9 to 12, give `regenerate`. After two failed retries on the same item, the verdict becomes `relayout` for 1 to 8, or a question to the owner for 9 to 12.
- Two or more failures in 13 to 17 give `regenerate`.
- Otherwise the verdict is `approved`, which still needs the owner's confirmation.
