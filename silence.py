import pydub
import pydub.silence
from pydub.silence import *


def detect_ending_silence(sound: pydub.AudioSegment, silence_threshold=-50.0, chunk_size=10):
    """
    Returns the millisecond/index that the ending silence starts.

    audio_segment - the segment to find silence in
    silence_threshold - the upper bound for how quiet is silent in dFBS
    chunk_size - chunk size for interating over the segment in ms
    """
    trim_ms = sound.duration_seconds * 1000 # ms
    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms-chunk_size:trim_ms].dBFS < silence_threshold and trim_ms > 0:
        trim_ms -= chunk_size

    # if there is no start it should return 0
    return min(max(0, trim_ms), sound.duration_seconds * 1000)


__all__ = [*list(filter(lambda x: not x.startswith("_"), dir(pydub.silence))), "detect_ending_silence"]