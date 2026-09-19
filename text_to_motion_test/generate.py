"""
Text -> motion test harness, model side: shells out to a local checkout of
GuyTevet/motion-diffusion-model (MDM) to sample a HumanML3D motion for a
text prompt, then converts its recover_from_ric() XYZ joint-position
output into the plain per-frame JSON preview.html reads.

This does NOT do VRM retargeting -- that happens in the browser
(preview.html), same division of labor as avatar_scene/convert_mixamo.html
(this side only produces/serves data; three.js does the actual retargeting
math client-side, using smpl_joints.py's skeleton metadata served via
/api/skeleton).

Prerequisites (not handled here -- follow MDM's own README):
  - A local clone of https://github.com/GuyTevet/motion-diffusion-model
    with its own conda env set up and dependencies installed.
  - A downloaded HumanML3D-pretrained checkpoint (e.g.
    save/humanml_trans_enc_512/model000200000.pt).
  - A CUDA-capable GPU -- CPU inference is technically possible but slow
    enough to not be worth it for interactive testing.

CLI usage:
    python generate.py --text "a person waves happily" \
        --mdm-repo /path/to/motion-diffusion-model \
        --model-path /path/to/save/humanml_trans_enc_512/model000200000.pt \
        --out outputs/wave.json

server.py calls run_mdm()/convert_to_frames() directly for the browser's
"Generate" button instead of shelling out to this file a second time.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from smpl_joints import JOINT_NAMES

DEFAULT_FPS = 20.0  # HumanML3D's native frame rate -- override with --fps if your checkpoint differs.


def run_mdm(mdm_repo: Path, model_path: Path, text_prompt: str, motion_length: float, seed: int, out_dir: Path) -> Path:
    """Runs MDM's own sample.generate CLI and returns the path to the
    results.npy it writes. Inherits stdout/stderr so MDM's own progress
    output (diffusion step count, sampling time, etc.) shows up live in
    whichever terminal is running this."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "sample.generate",
        "--model_path", str(model_path),
        "--text_prompt", text_prompt,
        "--num_samples", "1",
        "--num_repetitions", "1",
        "--motion_length", str(motion_length),
        "--seed", str(seed),
        "--output_dir", str(out_dir),
    ]
    print(f"Running in {mdm_repo}: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(mdm_repo))
    if result.returncode != 0:
        raise RuntimeError(f"MDM's sample.generate exited with code {result.returncode} -- see its output above.")

    results_path = out_dir / "results.npy"
    if not results_path.exists():
        raise RuntimeError(f"Expected {results_path} but MDM didn't produce it -- check its output above.")
    return results_path


def convert_to_frames(results_path: Path, fps: float) -> dict:
    """Loads MDM's results.npy (motion already converted to XYZ joint
    positions via recover_from_ric by MDM's own generate.py) and reshapes
    it into {"text", "fps", "joint_names", "frames": [frame][joint][xyz]}.
    """
    data = np.load(results_path, allow_pickle=True).item()
    motion = data["motion"]  # (num_samples, njoints, 3, seqlen)
    sample = motion[0]  # (njoints, 3, seqlen)
    length = int(data["lengths"][0]) if "lengths" in data else sample.shape[-1]
    njoints = sample.shape[0]

    if njoints != len(JOINT_NAMES):
        raise RuntimeError(
            f"Expected {len(JOINT_NAMES)} joints (HumanML3D), got {njoints} -- "
            "is this checkpoint trained on a different skeleton (e.g. KIT's 21 joints)?"
        )

    frames = [sample[:, :, f].tolist() for f in range(length)]  # each: njoints x [x, y, z]

    text = data.get("text")
    return {
        "text": text[0] if text else None,
        "fps": fps,
        "joint_names": JOINT_NAMES,
        "frames": frames,
    }


def generate(mdm_repo: Path, model_path: Path, text_prompt: str, motion_length: float, seed: int, fps: float) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        results_path = run_mdm(mdm_repo, model_path, text_prompt, motion_length, seed, Path(tmp))
        return convert_to_frames(results_path, fps)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--text", required=True, help="Text prompt to generate motion for.")
    parser.add_argument("--mdm-repo", required=True, type=Path, help="Path to your local motion-diffusion-model checkout.")
    parser.add_argument("--model-path", required=True, type=Path, help="Path to the .pt checkpoint.")
    parser.add_argument("--motion-length", type=float, default=4.0, help="Seconds of motion to generate (MDM's default max is ~9.8s).")
    parser.add_argument("--fps", type=float, default=DEFAULT_FPS, help="Frame rate of the checkpoint's dataset (20 for HumanML3D).")
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--out", required=True, type=Path, help="Where to write the converted joints JSON.")
    args = parser.parse_args()

    clip = generate(args.mdm_repo, args.model_path, args.text, args.motion_length, args.seed, args.fps)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(clip))
    print(f"Wrote {args.out} ({len(clip['frames'])} frames at {args.fps}fps).")


if __name__ == "__main__":
    main()
