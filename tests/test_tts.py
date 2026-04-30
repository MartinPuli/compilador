from pathlib import Path
import pytest

from morselang.tts import narrate_to_file, TTSClientProtocol, TTSError


class FakeClient:
    def __init__(self, audio_bytes: bytes = b"FAKE_MP3") -> None:
        self.audio_bytes = audio_bytes
        self.calls: list[dict] = []

    def synthesize(self, text: str, voice_id: str) -> bytes:
        self.calls.append({"text": text, "voice_id": voice_id})
        return self.audio_bytes


def test_narrate_to_file_writes_audio(tmp_path: Path):
    fake = FakeClient(audio_bytes=b"abc123")
    out = tmp_path / "out.mp3"
    narrate_to_file(["HOLA", "10"], voice_id="es-1", out_path=out, client=fake)
    assert out.read_bytes() == b"abc123"
    assert fake.calls == [{"text": "HOLA. 10.", "voice_id": "es-1"}]


def test_narrate_to_file_with_empty_lines_raises(tmp_path: Path):
    with pytest.raises(TTSError):
        narrate_to_file([], voice_id="es-1", out_path=tmp_path / "x.mp3", client=FakeClient())
