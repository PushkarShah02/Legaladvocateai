import type { Metadata } from 'next';
import localFont from 'next/font/local';
import Link from 'next/link';
import { Scale } from 'lucide-react';
import { ThemeProvider } from '@/components/app/theme-provider';
import { ThemeToggle } from '@/components/app/theme-toggle';
import '@/styles/globals.css';

const everett = localFont({
  src: '../public/everett-light.woff',
  variable: '--font-public-sans',
  display: 'swap',
});
const commitMono = localFont({
  src: '../fonts/CommitMono-400-Regular.otf',
  variable: '--font-commit-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'AI Advocate | Your voice workspace',
  description:
    'A thoughtful voice workspace to ask questions, explore ideas, and find clarity with your AI assistant.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${everett.variable} ${commitMono.variable} font-sans antialiased`}
    >
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <header className="advocate-header">
            <Link href="/" className="brand" aria-label="AI Advocate home">
              <span className="brand-mark">
                <Scale size={24} strokeWidth={1.5} />
              </span>
              <span>
                AI Advocate<span className="brand-caption">CLARITY THROUGH CONVERSATION</span>
              </span>
            </Link>
            <div className="header-tools">
              <span className="workspace-label">VOICE WORKSPACE</span>
              <ThemeToggle />
            </div>
          </header>
          {children}
          <footer className="advocate-footer">
            <span>
              AI Advocate <span aria-hidden="true">/</span> Your space for a clearer perspective.
            </span>
            <a href="https://livekit.io" target="_blank" rel="noreferrer">
              Voice powered by LiveKit ↗
            </a>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
