"""Opt-in offline LiveKit FFI probe; no room connection, credentials, or phone calls.

Run in an isolated process with: uv run python -X faulthandler scripts/probe-native-audio.py
A clean exit exercises only local audio objects, not the original connected-call crash.
"""

import asyncio
import json
from importlib.metadata import version

from livekit import rtc


async def main():
    for _ in range(20):
        source = rtc.AudioSource(48000, 1)
        track = rtc.LocalAudioTrack.create_audio_track("offline-native-probe", source)
        stream = rtc.AudioStream(track, sample_rate=48000, num_channels=1)
        try:
            frame = rtc.AudioFrame.create(48000, 1, 960)
            resampler = rtc.AudioResampler(48000, 16000)
            resampler.push(frame)
            resampler.flush()
            await source.capture_frame(frame)
            event = await asyncio.wait_for(stream.__anext__(), timeout=2)
            assert event.frame.samples_per_channel > 0
        finally:
            await stream.aclose()
            await source.aclose()
    print(json.dumps({"livekit": version("livekit"), "iterations": 20, "result": "passed"}))


if __name__ == "__main__":
    asyncio.run(main())
