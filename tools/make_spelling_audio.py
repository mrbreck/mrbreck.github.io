#!/usr/bin/env python3
"""Pre-record every word in HomeworkHelper/spelling-lists.js with a clear
neural voice (Kokoro af_heart), the way a teacher gives a spelling test:

    "The word is sword. The soldier carried a sharp sword. Sword."

Sentences come from tools/spelling-sentences.json; a word without one is
just said once.

Output: HomeworkHelper/audio/<hash>.mp3, where <hash> is the first 16 hex
chars of sha256("hh-audio::" + word). The page computes the same hash, so
file names never reveal the word.

Usage:
    pip install kokoro-onnx
    # model files: github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)
    python3 tools/make_spelling_audio.py --model-dir /path/to/kokoro [--force]

Words that already have a file are skipped unless --force is given.
Needs node (to read spelling-lists.js) and ffmpeg (to write mp3).
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess

import numpy as np
from kokoro_onnx import Kokoro

ROOT = pathlib.Path(__file__).resolve().parent.parent
LISTS_JS = ROOT / "HomeworkHelper" / "spelling-lists.js"
SENTENCES = ROOT / "tools" / "spelling-sentences.json"
OUT_DIR = ROOT / "HomeworkHelper" / "audio"

VOICE = "af_heart"
SPEED = 0.92           # a touch slower than normal, still natural
SAMPLE_RATE = 24000
SALT = "hh-audio::"

# Pronunciations to force, as phonemes (used everywhere the word is said).
PRONUNCIATIONS = {
    "lives": "lˈaɪvz",                       # plural of life, not "he lives"
    "mediterranean": "mˌɛdətəɹˈeɪniən",       # med-uh-tuh-RAY-nee-un
}


def audio_name(word: str) -> str:
    return hashlib.sha256((SALT + word).encode("utf-8")).hexdigest()[:16] + ".mp3"


def list_words() -> list[str]:
    js = (
        "global.window = {};"
        f"require({json.dumps(str(LISTS_JS))});"
        "const out = new Set();"
        "for (const l of window.HOMEWORK_HELPER_SPELLING_LISTS) {"
        "  for (const e of [...(l.words || []), ...(l.challenge || []), ...(l.content || [])])"
        "    for (const p of e.split('/')) if (p.trim()) out.add(p.trim().toLowerCase());"
        "}"
        "console.log(JSON.stringify([...out]));"
    )
    return json.loads(subprocess.check_output(["node", "-e", js], text=True))


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SAMPLE_RATE), dtype=np.float32)


def american(ph: str) -> str:
    # The phonemizer writes the "er/ir/ur" vowel British-style with no R
    # (sir -> "sɜː"); the American voice needs it R-colored ("sɜɹ").
    return re.sub(r"ɜː(?!ɹ)", "ɜɹ", ph)


def phonemes_for(kokoro: Kokoro, text: str) -> str:
    out = []
    for token in re.findall(r"[A-Za-z']+|[^A-Za-z']+", text):
        key = token.lower()
        if key in PRONUNCIATIONS:
            out.append(PRONUNCIATIONS[key])
        elif re.match(r"[A-Za-z']", token):
            out.append(american(kokoro.tokenizer.phonemize(token, "en-us")).strip())
        else:
            out.append(token)
    return "".join(out)


def script(word: str, sentence: str | None) -> str:
    # Never start the clip with the spelling word: this voice adds a little
    # "i" sound at the very start of a recording ("islurp" for slurp).
    if sentence:
        return f"The word is {word}. {sentence} {word.capitalize()}."
    return f"The word is {word}."


def record(kokoro: Kokoro, word: str, sentence: str | None) -> np.ndarray:
    # One pass over the whole clip: this voice garbles a word synthesized on
    # its own, but says it right with the rest of the clip around it.
    samples, sr = kokoro.create(phonemes_for(kokoro, script(word, sentence)),
                                voice=VOICE, speed=SPEED, lang="en-us", is_phonemes=True)
    assert sr == SAMPLE_RATE
    audio = samples.astype(np.float32)
    audio = audio / (float(np.max(np.abs(audio))) or 1.0) * 0.89  # about -1 dBFS
    # Lead-in because some speakers/Bluetooth clip the first moment.
    return np.concatenate([silence(0.15), audio, silence(0.25)]).astype(np.float32)


def write_mp3(samples: np.ndarray, path: pathlib.Path) -> None:
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y",
         "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "-",
         "-map_metadata", "-1", "-fflags", "+bitexact",
         "-codec:a", "libmp3lame", "-b:a", "64k", str(path)],
        input=samples.tobytes(), check=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", required=True, type=pathlib.Path)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    kokoro = Kokoro(str(args.model_dir / "kokoro-v1.0.onnx"),
                    str(args.model_dir / "voices-v1.0.bin"))
    sentences = json.loads(SENTENCES.read_text()) if SENTENCES.exists() else {}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    made = 0
    for word in list_words():
        path = OUT_DIR / audio_name(word)
        if path.exists() and not args.force:
            continue
        write_mp3(record(kokoro, word, sentences.get(word)), path)
        print(f"  {word:14s} {'with sentence' if word in sentences else 'word only'}", flush=True)
        made += 1

    # Manifest of which recordings exist (hashes only), so the page knows
    # up front whether to play a file or use the device voice.
    # Value is a short content hash, used as ?v= so a re-recorded clip is
    # never served stale from a browser cache.
    manifest = {p.stem: hashlib.sha256(p.read_bytes()).hexdigest()[:8]
                for p in sorted(OUT_DIR.glob("*.mp3"))}
    (OUT_DIR / "index.json").write_text(json.dumps(manifest) + "\n")
    print(f"recorded {made} word(s) into {OUT_DIR.relative_to(ROOT)} ({len(manifest)} total)")


if __name__ == "__main__":
    main()
