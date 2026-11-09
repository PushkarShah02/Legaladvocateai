"""Optional Anam output attached once to the existing voice session.

References: https://docs.livekit.io/agents/models/avatar/plugins/anam/
https://anam.ai/docs/integrations/livekit/configuration
"""

import asyncio
import logging
import os
import time

from livekit.plugins import anam

logger = logging.getLogger(__name__)


async def start_avatar(session, room):
    """Start before AgentSession.start; restore voice output on startup failure."""
    logger.info(
        "Anam initialization entered (worker PID=%s). Environment edits require an agent restart.",
        os.getpid(),
    )
    if os.getenv("ANAM_ENABLED", "true").strip().lower() in ("false", "0", "off"):
        logger.info("Anam disabled; using voice-only mode.")
        return None
    key = os.getenv("ANAM_API_KEY", "").strip()
    avatar_id = os.getenv("ANAM_AVATAR_ID", "").strip()
    logger.info(
        "Anam configuration: API key present=%s; avatar ID present=%s.",
        bool(key),
        bool(avatar_id),
    )
    if not key or not avatar_id:
        logger.warning(
            "ANAM_API_KEY and ANAM_AVATAR_ID are required for the avatar; using voice-only mode."
        )
        return None
    if not room.isconnected():
        logger.info(
            "No connected LiveKit room (for example terminal console); using voice-only mode."
        )
        return None

    original_audio = session.output.audio
    avatar = anam.AvatarSession(
        api_key=key,
        persona_config=anam.PersonaConfig(
            name=os.getenv("ANAM_AVATAR_NAME", "AI Advocate"),
            avatarId=avatar_id,
            avatarModel=os.getenv("ANAM_AVATAR_MODEL", "cara-4.1-express"),
        ),
    )
    started = time.monotonic()
    stage = "engine startup"
    logger.info("Anam engine startup requested; timeout=30s.")
    try:
        await asyncio.wait_for(avatar.start(session, room=room), timeout=30)
        stage = "video publication"
        logger.info("Anam engine accepted; waiting for avatar video; timeout=30s.")
        await avatar.wait_for_join(timeout=30)
    except (Exception, asyncio.CancelledError) as error:
        # Startup is before session.start, so no synchronizer/recorder wrappers
        # have been installed yet. Restore the complete original output safely.
        failed_audio = session.output.audio
        session.output.audio = original_audio
        try:
            await avatar.aclose()
            if failed_audio is not None and failed_audio is not original_audio:
                await failed_audio.aclose()
        except Exception as cleanup_error:
            raise RuntimeError(
                "Anam startup cleanup failed; restart the session or use ANAM_ENABLED=false."
            ) from cleanup_error
        if isinstance(error, asyncio.CancelledError):
            raise
        # Avoid logging provider response bodies or authentication headers.
        logger.warning(
            "Anam startup failed during %s (%s) after %.1fs; restored voice-only mode. Check Anam credentials, avatar access and account availability.",
            stage,
            type(error).__name__,
            time.monotonic() - started,
        )
        return None
    logger.info(
        "Anam avatar joined and published video after %.1fs. Audio is routed through the avatar; no second voice output is added.",
        time.monotonic() - started,
    )
    # SDK registers its own job shutdown callback to remove the participant.
    return avatar
