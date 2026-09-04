"""Batch pitch/EQ-adjusts a folder of dataset audio (e.g. a chosen LJSpeech
or single VCTK speaker's clips) BEFORE RVC training -- nudging the source
recordings' pitch/tone toward the target voice, so the trained model bakes
in the adjustment rather than needing it applied at conversion time.

Not part of the live app; run this once as a data-prep step, then upload
the output folder to the Kaggle training notebook.

Usage:
    python tools/prepare_voice_dataset.py INPUT_DIR OUTPUT_DIR \
        --pitch-semitones -3 --bass-gain-db 4
"""

import argparse
from pathlib import Path

import soundfile as sf
from pedalboard import Pedalboard, PitchShift, LowShelfFilter


def build_board(pitch_semitones: float, bass_gain_db: float) -> Pedalboard:
    effects = []
    if pitch_semitones:
        effects.append(PitchShift(semitones=pitch_semitones))
    if bass_gain_db:
        effects.append(LowShelfFilter(cutoff_frequency_hz=200.0, gain_db=bass_gain_db))
    return Pedalboard(effects)


def process_file(board: Pedalboard, in_path: Path, out_path: Path) -> None:
    audio, sample_rate = sf.read(str(in_path), dtype="float32", always_2d=True)
    processed = board(audio.T, sample_rate)  # pedalboard wants (channels, samples)
    sf.write(str(out_path), processed.T, sample_rate)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", help="Folder of source .wav dataset clips")
    parser.add_argument("output_dir", help="Folder to write adjusted clips to")
    parser.add_argument(
        "--pitch-semitones",
        type=float,
        default=0.0,
        help="Pitch shift in semitones, positive = up, negative = down",
    )
    parser.add_argument(
        "--bass-gain-db",
        type=float,
        default=0.0,
        help="Low-shelf gain below 200Hz in dB, positive = boost, negative = cut",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(input_dir.glob("*.wav"))
    if not wav_files:
        print(f"No .wav files found in {input_dir}")
        return

    board = build_board(args.pitch_semitones, args.bass_gain_db)

    for i, path in enumerate(wav_files, 1):
        out_path = output_dir / path.name
        process_file(board, path, out_path)
        print(f"[{i}/{len(wav_files)}] {path.name} -> {out_path}")

    print(f"Done: {len(wav_files)} file(s) written to {output_dir}")


if __name__ == "__main__":
    main()
