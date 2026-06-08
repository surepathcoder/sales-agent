import type { Metadata } from 'next';
import './globals.css';
import { Providers } from '@/components/providers';
import { ToastProvider } from '@/components/ui/toast';
import { PwaRegister } from '@/components/pwa-register';

export const metadata: Metadata = {
  title: 'Kijani AI — Agentic Sales for Tanzania',
  description: 'AI-powered B2B sales platform with WhatsApp-first outreach',
  manifest: '/manifest.json',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <Providers>
          <ToastProvider>
            <PwaRegister />
            {children}
          </ToastProvider>
        </Providers>
      </body>
    </html>
  );
}
