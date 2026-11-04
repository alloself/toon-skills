# Research: Blender layout plus video models

Collected November 2026. `toon-setup` turns this into the `pipeline-approach` rnd and one `evidence` doc per source.

## Findings

1. **A blockout is for space, not beauty.** Teams that use Blender for AI film keep the blockout low-poly. Extra detail misleads the model, and it copies what it sees. (flick.art; invideo blockout FAQs; tesseract.academy)
2. **A reference video transfers motion and camera together.** Seedance reference-video guides describe the video reference as the source of both movement and camera. A mannequin's stiff walk comes back as a stiff walk. (dev.to and apidog guides on Seedance 2.0 reference video; wavespeed.ai; nemovideo)
3. **Image references decide who is in frame; the video reference decides how things move.** Multimodal Seedance takes several images, videos and audio clips in one call and resolves them by role. (wavespeed.ai complete guide; lumalabs.ai basics; budgetpixel.com)
4. **Camera moves can be transferred on their own.** Runway documents applying a camera move from one clip to a new scene. That is the idea behind capsule references: keep the camera and paths, drop the acting. (help.runwayml.com)
5. **Start frames limit the shot.** A restyled start frame fixes the first pose, invents details and blocks turns and camera moves. It also costs one image generation per shot, often several. This finding came from the owner's animator and is the reason this pipeline has no keyframes.
6. **Seedance 2.5 makes multi-shot generation practical.** One call covers 4–30 s, so several short shots go into one generation instead of paying 4 s for each half-second shot. (Higgsfield `models_explore`)
7. **Motion control is a different tool.** Kling motion control and Higgsfield motion control copy a performance from a driving video onto a character. That is useful when a real actor performs the shot; it is not used for layout. (higgsfield.ai motion control guides; docs.imagine.art)
8. **Higgsfield's Blender plugin covers a similar idea inside Blender.** It sends the viewport to Seedance 2.5 and can animate a rig from text. It is out of scope for v1, see `optional-paths.md`. (higgsfield.ai/plugins/blender; rar.design guide)
9. **A local route exists.** ComfyUI with Wan 2.2 VACE takes depth or pose passes rendered from Blender. See `optional-paths.md`.

## Sources

| Short name | Locator |
|---|---|
| flick-blender-ai | https://flick.art/blog/blender-ai-filmmaking |
| invideo-blockout-camera | https://invideo.io/faq/how-do-you-use-a-blender-blocking-render-as-a-camera/ |
| invideo-blockout-lowpoly | https://invideo.io/faq/why-do-filmmakers-use-low-poly-blender-blockouts-as/ |
| invideo-blocking-vs-arrows | https://invideo.io/faq/blender-blocking-vs-storyboard-arrow-annotation-for-ai/ |
| tesseract-blender-ai | https://tesseract.academy/from-blender-to-ai-video-a-faster-creative-workflow/ |
| devto-seedance-refvideo | https://dev.to/apilover/how-to-use-reference-video-in-seedance-20-copy-motion-and-camera-moves-4o9d |
| apidog-seedance-refvideo | https://apidog.com/blog/use-seedance-2-0-reference-video |
| wavespeed-seedance-guide | https://wavespeed.ai/blog/posts/seedance-2-0-complete-guide-multimodal-video-creation/ |
| luma-seedance-basics | https://lumalabs.ai/learning-center/articles/seedance-2.0-basics |
| budgetpixel-seedance | https://budgetpixel.com/blog/seedance-20-the-reference-first-video-model-that-finally-feels-like-directing |
| runway-camera-transfer | https://help.runwayml.com/hc/en-us/articles/50488490233363 |
| higgsfield-blender-plugin | https://higgsfield.ai/plugins/blender |
| higgsfield-plugin-blog | https://higgsfield.ai/blog/higgsfield-blender-plugin |
| rar-plugin-guide | https://rar.design/posts/higgsfield-blender-plugin-guide |
| higgsfield-motion-control | https://higgsfield.ai/blog/Kling-2.6-Motion-Control-Full-Guide |
| comfy-seedance-r2v | https://www.comfy.org/workflows/api_seedance2_0_r2v-64f4db9e3e33/ |

## Patterns borrowed

- **Grilling**, from Matt Pocock's `grill-me` skill (github.com/mattpocock/skills). Ask one question at a time, always with a recommended answer. Walk the decision tree in dependency order. Answer from files instead of asking whenever possible. `toon-grill` applies it to the logic of a scene.
- **Document as you go**, from the Archcore skills (github.com/archcore-ai/archcore). Write typed docs, search before creating, start as draft and accept only on the owner's word.
