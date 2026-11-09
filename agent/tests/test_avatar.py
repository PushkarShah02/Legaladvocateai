import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from advocate.avatar import start_avatar


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("ANAM_API_KEY", "test-key-not-real")
    monkeypatch.setenv("ANAM_AVATAR_ID", "test-avatar")
    monkeypatch.setenv("ANAM_ENABLED", "true")


@pytest.mark.asyncio
async def test_missing_settings_preserve_voice(monkeypatch):
    monkeypatch.delenv("ANAM_API_KEY", raising=False)
    monkeypatch.delenv("ANAM_AVATAR_ID", raising=False)
    assert await start_avatar(None, None) is None


@pytest.mark.asyncio
async def test_disabled_preserves_voice(settings, monkeypatch):
    monkeypatch.setenv("ANAM_ENABLED", "false")
    assert await start_avatar(None, None) is None


@pytest.mark.asyncio
async def test_terminal_without_room_skips_avatar(settings):
    assert await start_avatar(None, SimpleNamespace(isconnected=lambda: False)) is None


@pytest.mark.asyncio
async def test_start_attaches_once_and_waits_for_video(settings, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="advocate.avatar")
    avatar = SimpleNamespace(
        start=AsyncMock(), wait_for_join=AsyncMock(), aclose=AsyncMock()
    )

    def factory(**kwargs):
        return avatar

    monkeypatch.setattr("advocate.avatar.anam.AvatarSession", factory)
    room = SimpleNamespace(isconnected=lambda: True)
    session = SimpleNamespace(output=SimpleNamespace(audio=None))
    assert await start_avatar(session, room) is avatar
    avatar.start.assert_awaited_once_with(session, room=room)
    avatar.wait_for_join.assert_awaited_once_with(timeout=30)
    avatar.aclose.assert_not_awaited()
    assert "API key present=True; avatar ID present=True" in caplog.text
    assert "waiting for avatar video" in caplog.text
    assert "joined and published video" in caplog.text
    assert "test-key-not-real" not in caplog.text
    assert "test-avatar" not in caplog.text


@pytest.mark.asyncio
async def test_failed_video_join_restores_audio_and_cleans_up(
    settings, monkeypatch, caplog
):
    original_audio = object()
    failed_audio = SimpleNamespace(aclose=AsyncMock())
    session = SimpleNamespace(output=SimpleNamespace(audio=original_audio))

    async def attach(*args, **kwargs):
        session.output.audio = failed_audio

    avatar = SimpleNamespace(
        start=AsyncMock(side_effect=attach),
        wait_for_join=AsyncMock(side_effect=TimeoutError("private-provider-body")),
        aclose=AsyncMock(),
    )
    monkeypatch.setattr("advocate.avatar.anam.AvatarSession", lambda **kwargs: avatar)
    assert (
        await start_avatar(session, SimpleNamespace(isconnected=lambda: True)) is None
    )
    assert session.output.audio is original_audio
    avatar.aclose.assert_awaited_once()
    failed_audio.aclose.assert_awaited_once()
    assert "failed during video publication (TimeoutError)" in caplog.text
    assert "private-provider-body" not in caplog.text
    assert "test-key-not-real" not in caplog.text
