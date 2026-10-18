"""
Quick check that the model backend configured in backend/.env actually works.

    python check_llm.py          # tests the LLM
    python check_llm.py --stt    # also loads the local speech-to-text model (downloads it the
                                 # first time, so do this once up front) and decodes a short
                                 # test sound the way a recorded answer is decoded

Run it from the backend/ folder with your environment active, before starting uvicorn.
"""

import math
import os
import struct
import sys
import tempfile
import time
import wave

from services import llm_service, stt_service


def _write_test_sound(path: str) -> None:
    """1.5 seconds of a 440 Hz tone as a plain WAV file (no speech in it)."""
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / 16000))) for i in range(24000)))


def main() -> int:
    print(f"Model backend:  {llm_service.describe_backend()}")
    print(f"Speech-to-text: {stt_service.describe_backend()}")
    print()

    print("Asking the model for a tiny JSON reply (the first call can take a minute while it loads)...")
    started = time.time()
    try:
        reply = llm_service.ping()
    except llm_service.LLMError as exc:
        print(f"FAILED: {exc}")
        return 1
    print(f"OK - model replied {reply} in {time.time() - started:.1f}s")

    if "--stt" in sys.argv:
        print()
        if not stt_service.describe_backend().startswith("local"):
            print("STT_PROVIDER isn't 'local' in .env, so there is nothing to load.")
        else:
            print("Loading the local Whisper model (the first run downloads it)...")
            started = time.time()
            try:
                stt_service.warm_up_local_model()
            except stt_service.STTError as exc:
                print(f"FAILED: {exc}")
                return 1
            print(f"OK - speech-to-text ready in {time.time() - started:.1f}s")

            # Loading the model is not enough: a recorded answer also has to be DECODED
            # (by the 'av' package), and a mismatched 'av' version fails only at that step.
            print("Decoding a short test sound the way a recorded answer is decoded...")
            folder = tempfile.mkdtemp()
            sound = os.path.join(folder, "test_tone.wav")
            try:
                _write_test_sound(sound)
                stt_service.transcribe_audio(sound)
            except Exception as exc:
                print(f"FAILED: {exc}")
                return 1
            finally:
                try:
                    os.remove(sound)
                    os.rmdir(folder)
                except OSError:
                    pass
            print("OK - recordings can be decoded (a tone has no words, so the transcript is empty)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
