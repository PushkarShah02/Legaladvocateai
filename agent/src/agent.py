import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    STTContextOptions,
    TurnHandlingOptions,
    cli,
    inference,
    room_io,
)
from livekit.plugins import ai_coustics

from advocate.avatar import start_avatar
from advocate.case import CaseState
from advocate.workflow import ConsultationAgent as Assistant

logger = logging.getLogger("agent")

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env.local")


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using AssemblyAI, Fish Audio, and the LiveKit turn detector
    state = CaseState(draft_directory=ROOT / "artifacts")

    async def publish_draft(text: str):
        await ctx.room.local_participant.send_text(text, topic="lk.chat")

    state.publish_text = publish_draft
    session = AgentSession[CaseState](
        userdata=state,
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=inference.STT(
            model=os.getenv("ADVOCATE_STT_MODEL", "assemblyai/universal-3-6-pro"),
            language="en",
        ),
        # Keyterms bias the STT toward distinctive words it would otherwise misspell.
        # List your own names, brands, and jargon in `keyterms`. Detection additionally
        # extracts terms from the live conversation, such as a caller's name, and applies
        # them once the transcript corroborates the spelling.
        # See more at https://docs.livekit.io/agents/models/stt/keyterms/
        stt_context_options=STTContextOptions(
            keyterms=["consumer", "refund", "National Consumer Helpline"],
            keyterm_detection={"enabled": True},
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=inference.TTS(
            model=os.getenv("ADVOCATE_TTS_MODEL", "fishaudio/s2.1-pro"),
            voice=os.getenv("ADVOCATE_TTS_VOICE", "fa4c9eb3dccc4806b382b40d61c6b10a"),
            language="en",
        ),
        turn_handling=TurnHandlingOptions(
            # The LiveKit turn detector determines when the user is done speaking and the agent should respond.
            # TurnDetector is an end-of-turn model that listens to the user's audio directly, combining
            # semantic understanding with acoustic cues (intonation, pitch, rhythm) for state-of-the-art accuracy.
            # AgentSession supplies the required VAD automatically.
            # See more at https://docs.livekit.io/agents/build/turns
            turn_detection=inference.TurnDetector(),
            # Adaptive interruptions use the turn detector to tell a real interruption from a
            # backchannel like "mhm" or "right", so the agent keeps talking through the latter.
            # This model is on by default on LiveKit Cloud and in dev mode. To use the model elsewhere,
            # uncomment the `interruption` line. Self-hosted usage past the monthly allowance is billed.
            # See https://docs.livekit.io/deploy/admin/quotas-and-limits/#adaptive-interruption-handling for more information.
            # interruption={"mode": "adaptive"},
            # allow the LLM to generate a response while waiting for the end of turn
            # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
            preemptive_generation={"enabled": False},
        ),
        # Expressive mode injects the TTS provider's markup guide into the LLM prompt, so the model
        # emits inline delivery tags (emotion, pacing, non-verbal sounds) that the TTS renders and
        # the transcript never shows. Requires a TTS model that supports markup, such as the Fish
        # Audio model above.
        expressive=True,
    )

    # Connect first so avatar startup can wait for its participant/video track.
    await ctx.connect()
    await start_avatar(session, ctx.room)

    # Start the existing session after Anam has attached its audio output.
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                ),
            ),
        ),
    )

    # Speak first: greet the user before they say anything
    await session.generate_reply(
        instructions="Speak only English. Say: Hi, I am your AI lawyer. What is your name? Do not add a licensing disclaimer or any other introduction."
    )


if __name__ == "__main__":
    cli.run_app(server)
