export type TranscriptEntry = {
  id: string;
  timestamp: number;
  speaker: 'You' | 'AI Advocate';
  text: string;
};

export type ConversationTranscript = {
  startedAt: string;
  endedAt?: string;
  entries: TranscriptEntry[];
};

export function formatTranscript(transcript: ConversationTranscript): string {
  const lines = [
    'AI Advocate — Conversation Transcript',
    `Started: ${transcript.startedAt}`,
    `Ended: ${transcript.endedAt ?? 'Conversation in progress'}`,
    '',
    'Text received during this browser session. Speech transcription may contain errors.',
    '',
  ];
  for (const entry of transcript.entries) {
    lines.push(`[${new Date(entry.timestamp).toISOString()}] ${entry.speaker}`, entry.text, '');
  }
  return lines.join('\n');
}

export function downloadTranscript(transcript: ConversationTranscript): void {
  const blob = new Blob([formatTranscript(transcript)], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `ai-advocate-transcript-${transcript.startedAt.replace(/[:.]/g, '-')}.txt`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Allow the browser to start reading before releasing the object URL.
  window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
