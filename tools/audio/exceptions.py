"""Audio mixer exceptions.

Defines the error hierarchy for audio mixer implementations.
These exceptions provide a public vocabulary for error handling
in concrete audio mixer implementations.
"""


class AudioError(Exception):
    """Base exception for audio errors.

    All audio-specific exceptions inherit from this class. Concrete mixer
    implementations should raise this or subclasses to indicate mixing failures.
    """

    pass


class AudioConfigError(AudioError):
    """Error in audio mixer configuration.

    Raised when a mixer receives an invalid or inconsistent configuration
    (e.g. negative sample rate, unsupported channel count).
    """

    pass


class AudioTrackError(AudioError):
    """Error loading or interpreting an audio track.

    Raised when a track's file cannot be opened, decoded, or its parameters
    are inconsistent with the mix configuration.
    """

    pass


class AudioMixError(AudioError):
    """Error during the mixing pass.

    Raised when the mixing process fails (e.g. incompatible sample rates
    between tracks, write failure).
    """

    pass
