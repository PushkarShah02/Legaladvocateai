'use client';

import { useEffect, useRef, useState } from 'react';
import { useSessionContext, useSessionMessages } from '@livekit/components-react';
import { Button } from '@/components/ui/button';
import {
  type ConversationTranscript,
  type TranscriptEntry,
  downloadTranscript,
} from '@/lib/transcript';

// This stays mounted when the call view closes, so disconnect cannot erase the export.
export function TranscriptDownload() {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const active = useRef(false);
  const startedAt = useRef('');
  const entries = useRef(new Map<string, TranscriptEntry>());
  const previousIds = useRef(new Set<string>());
  const excludedIds = useRef(new Set<string>());
  const [transcript, setTranscript] = useState<ConversationTranscript | null>(null);
  const [downloadError, setDownloadError] = useState(false);

  useEffect(() => {
    if (session.isConnected && !active.current) {
      active.current = true;
      startedAt.current = new Date().toISOString();
      entries.current.clear();
      excludedIds.current = new Set(previousIds.current);
      setTranscript(null);
      setDownloadError(false);
    }

    if (active.current) {
      for (const message of messages) {
        if (excludedIds.current.has(message.id) || !message.message.trim()) continue;
        // Streaming updates replace the same entry instead of duplicating partial text.
        entries.current.set(message.id, {
          id: message.id,
          timestamp: message.timestamp,
          speaker:
            message.type === 'userTranscript' || message.from?.isLocal ? 'You' : 'AI Advocate',
          text: message.message,
        });
      }
      const snapshot: ConversationTranscript = {
        startedAt: startedAt.current,
        entries: Array.from(entries.current.values()).sort((a, b) => a.timestamp - b.timestamp),
        ...(!session.isConnected ? { endedAt: new Date().toISOString() } : {}),
      };
      setTranscript(snapshot);
      if (!session.isConnected) {
        active.current = false;
        if (snapshot.entries.length) {
          try {
            downloadTranscript(snapshot);
          } catch {
            setDownloadError(true);
          }
        }
      }
    }
    // Remember prior IDs even if the SDK clears its arrays during disconnect.
    // Cached messages must never leak into the next call's transcript.
    for (const message of messages) previousIds.current.add(message.id);
  }, [session.isConnected, messages]);

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        variant="outline"
        size="sm"
        disabled={!transcript?.entries.length}
        onClick={() => {
          if (!transcript) return;
          try {
            downloadTranscript(transcript);
            setDownloadError(false);
          } catch {
            setDownloadError(true);
          }
        }}
      >
        Download transcript
      </Button>
      <p className="text-muted-foreground max-w-64 text-right text-xs" role="status">
        {downloadError
          ? 'Download failed. Please try the button again.'
          : transcript?.endedAt
            ? 'If no file appeared, download it here.'
            : 'Transcript downloads automatically when the call ends.'}
      </p>
    </div>
  );
}
