import type { Metadata, Viewport } from 'next';
import '../styles/globals.css';

export const metadata: Metadata = {
    title: 'Ultra-Fast Voice Agent',
    description: 'Real-time AI voice agent with sub-500ms latency using Pipecat and Google Gemini Live',
    keywords: ['voice AI', 'real-time', 'low latency', 'Gemini Live', 'Pipecat', 'voice assistant'],
    authors: [{ name: 'Voice Agent Team' }],
    manifest: '/manifest.json',
};

export const viewport: Viewport = {
    width: 'device-width',
    initialScale: 1,
    themeColor: '#10b981',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="dark">
            <head>
                <link rel="preconnect" href="https:
                <link
                    rel="preconnect"
                    href="https:
                    crossOrigin="anonymous"
                />
                <link
                    href="https:
                    rel="stylesheet"
                />
                <meta name="format-detection" content="telephone=no" />
                <meta name="mobile-web-app-capable" content="yes" />
                <meta name="apple-mobile-web-app-capable" content="yes" />
                <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

                {}
                <meta httpEquiv="X-DNS-Prefetch-Control" content="on" />
                <link rel="dns-prefetch" href="
                <link rel="dns-prefetch" href="

                {}
                <link rel="icon" href="/favicon.ico" />
                <link rel="apple-touch-icon" href="/icon-192x192.png" />
            </head>
            <body
                className="font-sans antialiased bg-background text-text-primary"
                style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
            >
                <div id="root" className="min-h-screen">
                    {children}
                </div>

                {}
                <script
                    dangerouslySetInnerHTML={{
                        __html: `

              if (typeof window !== 'undefined') {
                window.addEventListener('load', () => {
                  const loadTime = performance.now();
                  console.log('Page loaded in:', Math.round(loadTime), 'ms');

                  if ('PerformanceObserver' in window) {
                    const observer = new PerformanceObserver((list) => {
                      for (const entry of list.getEntries()) {
                        console.log(entry.name + ':', Math.round(entry.value), 'ms');
                      }
                    });
                    observer.observe({ entryTypes: ['measure', 'navigation'] });
                  }
                });
              }
            `,
                    }}
                />
            </body>
        </html>
    );
}
