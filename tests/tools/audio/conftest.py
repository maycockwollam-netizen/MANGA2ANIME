"""Shared fixtures for audio tests."""

from __future__ import annotations

import struct
import wave
from collections.abc import Callable
from pathlib import Path

import pytest


def _write_wav(
    path: Path,
    *,
    sample_rate: int = 44100,
    channels: int = 1,
    duration_seconds: float = 0.1,
    value: int = 16000,
) -> None:
    """Write a constant-value PCM 16-bit WAV file."""
    frames = int(duration_seconds * sample_rate)
    samples = [value] * (frames * channels)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


@pytest.fixture
def make_wav(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that writes a WAV file into tmp_path."""
    counter = {"n": 0}

    def _factory(
        name: str | None = None,
        *,
        sample_rate: int = 44100,
        channels: int = 1,
        duration_seconds: float = 0.1,
        value: int = 16000,
    ) -> Path:
        counter["n"] += 1
        fname = name or f"track_{counter['n']}.wav"
        path = tmp_path / fname
        _write_wav(
            path,
            sample_rate=sample_rate,
            channels=channels,
            duration_seconds=duration_seconds,
            value=value,
        )
        return path

    return _factory
