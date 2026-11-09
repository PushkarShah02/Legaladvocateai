"""Generate listening previews using the configured voice; no avatar is started."""

import asyncio
import os
import wave
from pathlib import Path

import aiohttp
from dotenv import load_dotenv
from livekit.agents import inference

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env.local")


async def main():
    directory = ROOT / "test-results" / "voice-language"
    directory.mkdir(parents=True, exist_ok=True)
    samples = {"english": "Hi, I am your AI lawyer. What is your name?"}
    async with (
        aiohttp.ClientSession() as http,
        inference.TTS(
            model=os.getenv("ADVOCATE_TTS_MODEL", "fishaudio/s2.1-pro"),
            voice=os.getenv("ADVOCATE_TTS_VOICE", "fa4c9eb3dccc4806b382b40d61c6b10a"),
            language="en",
            http_session=http,
        ) as tts,
    ):
        for name, text in samples.items():
            frames = []
            async with tts.stream() as stream:
                stream.push_text(text)
                stream.end_input()
                async for event in stream:
                    frames.append(event.frame)
            if not frames:
                raise RuntimeError(f"No audio received for {name}")
            path = directory / f"{name}.wav"
            with wave.open(str(path), "wb") as output:
                output.setnchannels(frames[0].num_channels)
                output.setsampwidth(2)
                output.setframerate(frames[0].sample_rate)
                for frame in frames:
                    output.writeframes(frame.data)
            print(f"Generated {name}: {path}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
