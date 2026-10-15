#!/usr/bin/env python3
"""Pre-record every word in HomeworkHelper/spelling-lists.js with a clear
neural voice (Kokoro af_heart: warm, clear, kid-appropriate).

Output: HomeworkHelper/audio/<hash>.mp3, where <hash> is the first 16 hex
chars of sha256("hh-audio::" + word). The page computes the same hash, so
file names never reveal the word.

Usage:
    pip install kokoro-onnx sherpa-onnx
    # Kokoro model files: github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)
    # Checker: github.com/k2-fsa/sherpa-onnx/releases (asr-models, whisper-small.en)
    python3 tools/make_spelling_audio.py --model-dir /path/to/kokoro \
        [--check-model /path/to/sherpa-onnx-whisper-small.en] [--force]

With --check-model, each recording is played to a speech recognizer as
"The word is ___". If it isn't heard as the right word (or a soundalike,
e.g. feet/feat), the word is re-recorded at a different pace until it is.

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
OUT_DIR = ROOT / "HomeworkHelper" / "audio"

# Don't blend in af_nicole: it's a breathy, whispery voice.
VOICE_BLEND = {"af_heart": 1.0}
# Only for a word that no af_heart take gets right (its F can sound like V).
BACKUP_BLEND = {"af_heart": 0.7, "af_sarah": 0.3}
SAMPLE_RATE = 24000
# Tried in order until the checker hears the word right. Slightly slow first,
# since that's easiest for kids to catch.
TAKES = [
    dict(speed=0.85, punct=""),
    dict(speed=0.95, punct=""),
    dict(speed=1.0, punct=""),
    dict(speed=0.9, punct="."),
    dict(speed=0.8, punct=""),
    dict(speed=0.85, punct="", blend=BACKUP_BLEND),
    dict(speed=0.95, punct="", blend=BACKUP_BLEND),
]
SALT = "hh-audio::"

# Words whose default pronunciation is wrong for the list (homographs).
# Value is the phoneme string to speak instead.
PRONUNCIATIONS = {
    "lives": "lˈaɪvz",  # plural of life, not "he lives"
}


def audio_name(word: str) -> str:
    return hashlib.sha256((SALT + word).encode("utf-8")).hexdigest()[:16] + ".mp3"


def list_words() -> list[str]:
    js = (
        "global.window = {};"
        f"require({json.dumps(str(LISTS_JS))});"
        "const out = new Set();"
        "for (const l of window.HOMEWORK_HELPER_SPELLING_LISTS) {"
        "  for (const e of [...(l.words || []), ...(l.challenge || [])])"
        "    for (const p of e.split('/')) if (p.trim()) out.add(p.trim().toLowerCase());"
        "}"
        "console.log(JSON.stringify([...out]));"
    )
    return json.loads(subprocess.check_output(["node", "-e", js], text=True))


def dictation_phonemes(kokoro: Kokoro, word: str) -> str:
    if word in PRONUNCIATIONS:
        return PRONUNCIATIONS[word]
    ph = kokoro.tokenizer.phonemize(word, "en-us")
    # American English turns t/d between vowels into a flap that sounds the
    # same for both ("submitting" -> "submidding"). For dictation, say the
    # consonant the way it's spelled.
    if "ɾ" in ph:
        ph = ph.replace("ɾ", "t" if "t" in word else "d")
    return ph


def voice_style(kokoro: Kokoro, blend: dict) -> np.ndarray:
    return sum(w * kokoro.get_voice_style(v) for v, w in blend.items())


def say(kokoro: Kokoro, phonemes: str, speed: float, blend: dict = VOICE_BLEND) -> np.ndarray:
    samples, sr = kokoro.create(phonemes, voice=voice_style(kokoro, blend), speed=speed,
                                lang="en-us", is_phonemes=True)
    assert sr == SAMPLE_RATE
    peak = float(np.max(np.abs(samples))) or 1.0
    return (samples / peak * 0.89).astype(np.float32)  # about -1 dBFS


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SAMPLE_RATE), dtype=np.float32)


def pad(samples: np.ndarray) -> np.ndarray:
    # Lead-in because some speakers/Bluetooth clip the first moment.
    return np.concatenate([silence(0.15), samples, silence(0.25)])


class Checker:
    """Plays a take to Whisper as "The word is <take>" and reports what it heard."""

    def __init__(self, model_dir: pathlib.Path, kokoro: Kokoro):
        import sherpa_onnx
        name = model_dir.name.replace("sherpa-onnx-whisper-", "")
        enc = model_dir / f"{name}-encoder.int8.onnx"
        dec = model_dir / f"{name}-decoder.int8.onnx"
        if not enc.exists():
            enc, dec = model_dir / f"{name}-encoder.onnx", model_dir / f"{name}-decoder.onnx"
        self.rec = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=str(enc), decoder=str(dec), tokens=str(model_dir / f"{name}-tokens.txt"),
            language="en", task="transcribe", num_threads=2)
        self.kokoro = kokoro
        self.carrier = say(kokoro, kokoro.tokenizer.phonemize("The word is", "en-us"), 0.95)

    def heard(self, take: np.ndarray) -> str:
        audio = np.concatenate([self.carrier, silence(0.35), take, silence(0.6)])
        audio16 = np.interp(np.arange(0, len(audio), SAMPLE_RATE / 16000),
                            np.arange(len(audio)), audio).astype(np.float32)
        stream = self.rec.create_stream()
        stream.accept_waveform(16000, audio16)
        self.rec.decode_stream(stream)
        text = re.sub(r"[^a-z' ]", " ", stream.result.text.lower())
        if "word is" in text:
            text = text.rsplit("word is", 1)[1]
        words = text.split()
        while len(words) > 1 and words[0] in ("a", "an", "the"):
            words.pop(0)  # "the word is a thief" still counts
        return " ".join(words)

    def ok(self, word: str, heard: str) -> bool:
        if heard == word:
            return True
        # Soundalikes count (feet/feat, nights/knights): same phonemes.
        ph = lambda w: self.kokoro.tokenizer.phonemize(w, "en-us").replace("ˈ", "").replace("ˌ", "")
        return bool(heard) and ph(heard) == ph(word)


def record(kokoro: Kokoro, word: str, checker: "Checker | None") -> tuple[np.ndarray, str]:
    phonemes = dictation_phonemes(kokoro, word)
    first = None
    for take in TAKES:
        samples = say(kokoro, phonemes + take["punct"], take["speed"],
                      take.get("blend", VOICE_BLEND))
        if checker is None:
            return samples, "unchecked"
        heard = checker.heard(samples)
        if first is None:
            first = (samples, heard)
        if checker.ok(word, heard):
            return samples, (f"ok at speed {take['speed']}"
                             f"{' with stop' if take['punct'] else ''}"
                             f"{' (backup voice)' if 'blend' in take else ''}")
    return first[0], f"CHECK FAILED (heard {first[1]!r}); kept first take"


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
    ap.add_argument("--check-model", type=pathlib.Path)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    kokoro = Kokoro(str(args.model_dir / "kokoro-v1.0.onnx"),
                    str(args.model_dir / "voices-v1.0.bin"))
    checker = Checker(args.check_model, kokoro) if args.check_model else None
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    made = 0
    for word in list_words():
        path = OUT_DIR / audio_name(word)
        if path.exists() and not args.force:
            continue
        samples, note = record(kokoro, word, checker)
        write_mp3(pad(samples), path)
        print(f"  {word:14s} {note}", flush=True)
        made += 1

    # Manifest of which recordings exist (hashes only), so the page knows
    # up front whether to play a file or use the device voice.
    names = sorted(p.stem for p in OUT_DIR.glob("*.mp3"))
    (OUT_DIR / "index.json").write_text(json.dumps(names) + "\n")
    print(f"recorded {made} word(s) into {OUT_DIR.relative_to(ROOT)} ({len(names)} total)")


if __name__ == "__main__":
    main()
