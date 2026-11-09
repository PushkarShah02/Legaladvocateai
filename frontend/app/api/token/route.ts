import { NextResponse } from 'next/server';
import { AccessToken, RoomAgentDispatch, RoomConfiguration } from 'livekit-server-sdk';
import { randomUUID } from 'node:crypto';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
const responseHeaders = { 'Cache-Control': 'no-store' };

// Public access is intentional. Only the server chooses the room and deployed agent.
export async function POST(req: Request) {
  const origin = req.headers.get('origin');
  if (
    req.headers.get('sec-fetch-site') === 'cross-site' ||
    (origin && origin !== new URL(req.url).origin)
  ) {
    return NextResponse.json(
      { error: 'Request origin is not allowed.' },
      { status: 403, headers: responseHeaders }
    );
  }
  const apiKey = process.env.LIVEKIT_API_KEY?.trim();
  const apiSecret = process.env.LIVEKIT_API_SECRET?.trim();
  const serverUrl = process.env.LIVEKIT_URL?.trim();
  const agentName = process.env.AGENT_NAME?.trim() || 'my-agent';
  if (!apiKey || !apiSecret || !serverUrl) {
    console.error('LiveKit token endpoint: required server configuration is missing.');
    return NextResponse.json(
      { error: 'Voice service is not configured.' },
      { status: 503, headers: responseHeaders }
    );
  }
  try {
    const url = new URL(serverUrl);
    if (url.protocol !== 'wss:' || !url.hostname.endsWith('.livekit.cloud')) {
      return NextResponse.json(
        { error: 'Voice service configuration is invalid.' },
        { status: 503, headers: responseHeaders }
      );
    }
    const roomName = `advocate-${randomUUID()}`;
    const participantName = 'user';
    const token = new AccessToken(apiKey, apiSecret, {
      identity: `user-${randomUUID()}`,
      name: participantName,
      ttl: '15m',
    });
    token.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canPublishData: true,
      canSubscribe: true,
    });
    // Ignore client room_config: always use the configured agent's production deployment.
    token.roomConfig = new RoomConfiguration({ agents: [new RoomAgentDispatch({ agentName })] });
    const participantToken = await token.toJwt();
    return NextResponse.json(
      { serverUrl, roomName, participantName, participantToken },
      { headers: responseHeaders }
    );
  } catch {
    // Never print environment values, JWTs, request bodies or raw SDK errors.
    console.error('LiveKit token endpoint: token generation failed.');
    return NextResponse.json(
      { error: 'Unable to start a voice session. Please try again.' },
      { status: 500, headers: responseHeaders }
    );
  }
}
