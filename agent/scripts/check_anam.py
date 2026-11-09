"""Check configured Anam avatar access without starting a billable video session."""

import asyncio
import os
from pathlib import Path
from uuid import UUID

import aiohttp
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")


async def check():
    key = os.getenv("ANAM_API_KEY", "").strip()
    avatar_id = os.getenv("ANAM_AVATAR_ID", "").strip()
    print(f"ANAM_API_KEY populated: {bool(key)}")
    print(f"ANAM_AVATAR_ID populated: {bool(avatar_id)}")
    if not key or not avatar_id:
        return False
    try:
        UUID(avatar_id)
    except ValueError:
        print("ANAM_AVATAR_ID must be the avatar UUID, not its display name or URL.")
        return False
    try:
        async with (
            aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session,
            session.get(
                f"https://api.anam.ai/v1/avatars/{avatar_id}",
                headers={"Authorization": f"Bearer {key}"},
                allow_redirects=False,
            ) as response,
        ):
            print(f"Anam avatar access HTTP status: {response.status}")
            if response.status != 200:
                print(
                    "Check API key, avatar ID and account access. Response body omitted to protect credentials."
                )
                return False
            result = await response.json()
            print(f"Avatar returned by official API: {bool(result)}")
            return True
    except (aiohttp.ClientError, TimeoutError) as error:
        print(
            f"Anam access check failed: {type(error).__name__}. No credentials printed."
        )
        return False


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(check()) else 1)
