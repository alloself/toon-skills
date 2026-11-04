# Optional paths, outside v1

These routes are not used by the toon skills. They are listed so a project can choose one deliberately.

## Higgsfield Blender plugin

Higgsfield ships a Blender add-on for Blender 4.2 to 5.1. Source: https://higgsfield.ai/plugins/blender. Its tabs are:
- Scene builder
- 3D model (Meshy)
- Character animation, which turns text into keys on a rig
- Image
- Video, which sends the viewport to Seedance 2.5 with an anti-slop option
- Camera, which records phone motion into a camera
- Asset

It also exposes an MCP bridge at `https://bridge.higgsfield.ai/mcp`.

- **When it helps:** quick one-off shots made entirely inside Blender, or recording a hand-held camera move with a phone.
- **Why not v1:** it renders what the viewport shows, so mannequins and their motion go to the model unless you hide them yourself. It also runs inside one Blender, while the toon skills work from any client over any Blender access.
- **To combine:** use its Camera tab to record a camera, keep layout and references in toon-layout, and generate with toon-sequence.

## ComfyUI with Wan 2.2 VACE

A local route on your own GPU. Blender renders depth, normal or OpenPose passes per shot, and VACE generates video that follows them.

- **When it helps:** no credits to spend, full control, and long series on local hardware.
- **Cost:** you build and tune the workflow, quality and character consistency depend on your LoRAs, and per-shot passes bring back the per-shot work.
- **To combine:** `toon_blender` already knows shots, cameras and cast. A pass exporter would be one more mode in `export`.

## Motion control

Higgsfield `motion_control` and Kling motion control copy a performance from a driving video onto a character image.

- **When it helps:** a real person acts out a hard shot, such as a dance, a fall or a specific gesture, and the character must follow it exactly.
- **Cost:** it is one shot at a time with a start image, which is the approach this pipeline avoids for normal shots.
