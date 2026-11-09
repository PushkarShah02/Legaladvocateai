import { ArrowRight, AudioLines, BookOpen, MessageSquareText, Mic, Scale } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => (
  <div ref={ref} className="advocate-welcome">
    <section className="conversation-card">
      <div className="card-eyebrow">
        <span className="status-dot" /> YOUR VOICE WORKSPACE
      </div>
      <div className="voice-emblem" aria-hidden="true">
        <Scale size={40} strokeWidth={1.3} />
      </div>
      <span className="eyebrow">A little clarity goes a long way.</span>
      <h2>Let’s talk it through.</h2>
      <p>
        Bring your questions. Explore the details. Move forward with a clearer understanding, one
        conversation at a time.
      </p>
      <Button size="lg" onClick={onStartCall} className="conversation-start">
        <Mic size={18} />
        {startButtonText}
        <ArrowRight size={18} />
      </Button>
      <span className="microphone-note">Your browser will ask for microphone access.</span>
      <div className="conversation-card-footer">
        <AudioLines size={16} />
        <span>Natural conversation</span>
        <span className="footer-divider" />
        <MessageSquareText size={16} />
        <span>Live transcript</span>
      </div>
    </section>
    <aside className="workspace-guide">
      <div className="guide-heading">
        <BookOpen size={19} />
        <h3>A space to find perspective</h3>
      </div>
      <p>Start with what’s on your mind. You don’t need to have all the right words.</p>
      <div className="guide-step">
        <span>01</span>
        <div>
          <h4>Share your question</h4>
          <p>Give your assistant a little context and tell it what you’d like to understand.</p>
        </div>
      </div>
      <div className="guide-step">
        <span>02</span>
        <div>
          <h4>Explore it together</h4>
          <p>Ask follow-up questions, interrupt naturally, or switch to text chat.</p>
        </div>
      </div>
      <div className="guide-step">
        <span>03</span>
        <div>
          <h4>Leave with clarity</h4>
          <p>Use the live transcript to revisit the details during your conversation.</p>
        </div>
      </div>
      <div className="guide-note">
        <span className="eyebrow">BEFORE YOU BEGIN</span>
        <p>
          This is an AI assistant for general information. It does not replace advice from a
          qualified advocate.
        </p>
      </div>
    </aside>
  </div>
);
