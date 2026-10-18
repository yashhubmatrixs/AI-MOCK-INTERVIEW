"""
Speech-to-text for "verbal" answers.

The browser records the answer (MediaRecorder), uploads the file once the
candidate stops speaking, and this module turns it into text in one call
(deliberately not streaming - see the README "Real-time, honestly" section).

STT_PROVIDER in backend/.env picks the engine:

  openai  (default)  OpenAI's hosted Whisper. Needs OPENAI_API_KEY and prepaid credit.
  local              faster-whisper running on this machine. Free and offline after a
                     one-time model download:  pip install -r requirements-local.txt
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class STTError(Exception):
    """Transcription failed. The message is safe to show to the user."""


def _provider() -> str:
    value = os.getenv("STT_PROVIDER", "openai").strip().lower()
    if value not in ("openai", "local"):
        raise STTError(f"STT_PROVIDER in backend/.env must be 'openai' or 'local' (got '{value}').")
    return value


def describe_backend() -> str:
    """One-line description for the startup log and check_llm.py."""
    try:
        if _provider() == "local":
            size = os.getenv("WHISPER_MODEL_SIZE", "base")
            lang = os.getenv("WHISPER_LANGUAGE", "en") or "auto-detect"
            return f"local - faster-whisper '{size}' (language: {lang})"
        return f"openai - model '{os.getenv('STT_MODEL', 'whisper-1')}'"
    except STTError as exc:
        return f"misconfigured - {exc}"


def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file on disk (webm/mp3/wav/m4a) to plain text."""
    if _provider() == "local":
        return _transcribe_local(file_path)
    return _transcribe_openai(file_path)


# ---------------------------------------------------------------------------
# OpenAI hosted Whisper
# ---------------------------------------------------------------------------

_openai_client = None


def _transcribe_openai(file_path: str) -> str:
    global _openai_client
    # Imported here so running purely locally never depends on the OpenAI SDK.
    try:
        import openai
    except ImportError:
        raise STTError("The 'openai' package isn't installed. Run: pip install -r requirements.txt")

    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise STTError(
                "OPENAI_API_KEY isn't set in backend/.env. Add one, or transcribe on this "
                "machine instead by setting STT_PROVIDER=local."
            )
        _openai_client = openai.OpenAI(api_key=api_key)

    try:
        with open(file_path, "rb") as audio_file:
            transcript = _openai_client.audio.transcriptions.create(
                model=os.getenv("STT_MODEL", "whisper-1"),
                file=audio_file,
            )
    except openai.RateLimitError as exc:
        if "insufficient_quota" in str(exc):
            raise STTError(
                "OpenAI says this API key has no credit left (insufficient_quota). Add "
                "credit, or transcribe on this machine instead with STT_PROVIDER=local."
            )
        raise STTError("OpenAI is rate-limiting requests right now. Wait a few seconds and try again.")
    except openai.AuthenticationError:
        raise STTError("OpenAI rejected the API key. Check OPENAI_API_KEY in backend/.env.")
    except openai.APIConnectionError:
        raise STTError("Couldn't reach OpenAI. Check your internet connection.")
    except openai.OpenAIError as exc:
        raise STTError(f"OpenAI error: {exc}")
    return transcript.text.strip()


# ---------------------------------------------------------------------------
# Local faster-whisper
# ---------------------------------------------------------------------------

_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise STTError(
                "Local transcription needs the 'faster-whisper' package. "
                "Run: pip install -r requirements-local.txt"
            )
        size = os.getenv("WHISPER_MODEL_SIZE", "base")
        try:
            # CPU + int8 runs on any laptop. The first call downloads the model once.
            _local_model = WhisperModel(size, device="cpu", compute_type="int8")
        except Exception as exc:
            raise STTError(
                f"Couldn't load the Whisper '{size}' model ({exc}). The first run needs an "
                "internet connection to download it."
            )
    return _local_model


def warm_up_local_model() -> None:
    """Load (and if needed download) the local model now instead of on the first answer."""
    _get_local_model()


def _transcribe_local(file_path: str) -> str:
    model = _get_local_model()
    # Forcing English avoids Whisper guessing the wrong language on short clips.
    language = os.getenv("WHISPER_LANGUAGE", "en") or None
    try:
        segments, _info = model.transcribe(file_path, language=language, beam_size=1)
        return " ".join(segment.text.strip() for segment in segments).strip()
    except Exception as exc:
        if "metadata_errors" in str(exc):
            # faster-whisper calls av.open(metadata_errors=...). 'av' 19 removed that argument
            # (and very old versions never had it), so only some versions work together.
            raise STTError(
                "Couldn't transcribe that recording: the installed 'av' audio package doesn't match "
                "faster-whisper. Run: pip install \"av>=13,<19\"   (then restart the backend)"
            )
        raise STTError(f"Couldn't transcribe that recording: {exc}")
