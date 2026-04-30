"""ElevenLabs text-to-speech client (thin wrapper).

`narrate_to_file` takes the interpreter's output buffer, joins it into a
narration string, calls a TTS client (real or fake), and writes an MP3 to
disk. The real client is constructed lazily so missing API keys don't
break unrelated test runs.
"""

from pathlib import Path
from typing import Protocol


class TTSError(Exception):
    pass


class TTSClientProtocol(Protocol):
    def synthesize(self, text: str, voice_id: str) -> bytes: ...


def narrate_to_file(
    lines: list[str],
    *,
    voice_id: str,
    out_path: Path,
    client: TTSClientProtocol,
) -> None:
    if not lines:
        raise TTSError("No hay salida para narrar — el programa no produjo MOSTRAR.")
    text = ". ".join(lines) + "."
    audio = client.synthesize(text, voice_id=voice_id)
    out_path.write_bytes(audio)


def make_default_client(api_key: str) -> TTSClientProtocol:
    """Construct the real ElevenLabs-backed client. Lazy import keeps the
    SDK out of every test run."""
    from elevenlabs.client import ElevenLabs

    sdk = ElevenLabs(api_key=api_key)

    class _RealClient:
        def synthesize(self, text: str, voice_id: str) -> bytes:
            stream = sdk.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
            )
            return b"".join(stream)

    return _RealClient()
