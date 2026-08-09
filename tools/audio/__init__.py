"""Audio Mixer Integration Contract.

Defines the minimal contract for audio mixing of tracks placed on a shared
timeline. This module specifies what data an audio mixer consumes and
produces, without knowing how mixing is performed.

This module does NOT:
- Implement mixing (delegated to concrete_mixer.py)
- Access GPU
- Execute animation logic
- Depend on runtime.animation internals

Architecture:
    tools/audio/models.py (AudioTrack, MixConfig, MixResult)
            ↓
    tools/audio/protocol.py (AudioMixer Protocol)
            ↓
    tools/audio/adapter.py (OutputAdapter)
            ↓
    [Concrete Mixer Implementations]

Dependency Constraints:
    The AudioMixer protocol and its models must NOT depend on:
    - runtime.animation (ANY module)
    - AnimationRuntime internals
    - AnimationTimeline / AnimationClip
    - tools.manga_frame
"""

from __future__ import annotations

from tools.audio.adapter import OutputAdapter as OutputAdapter  # noqa: E402
from tools.audio.concrete_mixer import WaveMixer as WaveMixer  # noqa: E402
from tools.audio.exceptions import (  # noqa: E402
    AudioConfigError,
    AudioError,
    AudioMixError,
    AudioTrackError,
)
from tools.audio.models import (  # noqa: E402
    AudioTrack,
    MixConfig,
    MixResult,
)
from tools.audio.protocol import AudioMixer as AudioMixer  # noqa: E402

__all__ = [
    # Core data contracts
    "AudioTrack",
    "MixConfig",
    "MixResult",
    # Audio mixer protocol
    "AudioMixer",
    # Audio mixer adapter
    "OutputAdapter",
    # Concrete audio mixer
    "WaveMixer",
    # Audio errors
    "AudioError",
    "AudioConfigError",
    "AudioMixError",
    "AudioTrackError",
]
