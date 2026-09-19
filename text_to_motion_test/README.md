# text_to_motion_test/

A standalone test harness for [MDM (Human Motion Diffusion Model)](https://github.com/GuyTevet/motion-diffusion-model)
-- type a text prompt, generate a motion, preview it on your VRM model.
This is deliberately separate from `avatar_scene/` and `lib/motion/`: it's
for judging whether MDM's output is good enough to build the real
in-app "generate a clip the classifier couldn't match" feature on top of,
not a finished pipeline yet.

## What this does and doesn't do

- Generates raw motion from text via MDM, running on your GPU.
- Retargets it onto your VRM **approximately**, in the browser: MDM only
  outputs joint XYZ *positions* (no bone rotations), so `preview.html`
  derives each bone's rotation from parent->child direction vectors,
  relative to the clip's own first frame. This captures swing (which way
  a limb points) but not twist (rotation around the limb's own axis),
  and frame 0 of every retargeted clip is, by construction, your VRM's
  rest pose -- you're judging the *shape* of the generated motion, not
  its absolute starting stance. Good enough to see if a gesture reads
  right; not the rigorous retarget `avatar_scene/convert_mixamo.html`
  does for real mocap (which has actual per-bone rotation tracks to work
  with, not just positions).
- Does **not** save anything into `lib/motion/clips/`. If a generation
  looks good and you want to promote it into the real library, that's a
  separate step to build once you've judged the model's worth it.

## Prerequisites (do this yourself -- not handled by anything here)

1. Clone MDM somewhere and follow its own README to set up the environment:
   ```
   git clone https://github.com/GuyTevet/motion-diffusion-model
   ```
   It needs its own Python env (conda recommended -- MDM pins specific
   versions of torch, clip, spacy, chumpy, etc.) and a CUDA-capable GPU.
2. Download a HumanML3D-pretrained checkpoint per MDM's README (e.g.
   `save/humanml_trans_enc_512/model000200000.pt`) into that checkout.
3. Confirm MDM works standalone first:
   ```
   python -m sample.generate --model_path <path to .pt> --text_prompt "a person waves"
   ```
   from inside the MDM repo, using MDM's own conda env. Don't move on to
   this test tool until that works on its own.

## Running this tool

From this repo's own Python environment (needs `numpy`, already in
`requirements.txt`):

```
python server.py --mdm-repo /path/to/motion-diffusion-model --model-path /path/to/save/humanml_trans_enc_512/model000200000.pt
```

Then open `http://localhost:8090/preview.html`, load your VRM (defaults
to `../avatar_scene/models/placeholder.vrm`), type a prompt, and hit
Generate. This shells out to MDM's own `sample.generate` under the hood
(same command as step 3 above) -- watch the terminal running `server.py`
for MDM's own progress output.

Note: `server.py` and MDM's own environment are almost certainly
different Python environments (this repo's vs. MDM's conda env). If
`server.py`'s `sys.executable` (used to invoke `python -m sample.generate`)
doesn't have MDM's dependencies installed, generation will fail --
either run `server.py` itself from within MDM's conda env, or adjust
`generate.py`'s `run_mdm()` to invoke that env's Python explicitly.

Generated clips are cached as JSON under `outputs/` (gitignored) so you
can flip back through past prompts without regenerating.
