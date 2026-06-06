import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between px-8 py-6">
        <span className="text-2xl font-bold text-kijani-700">🌿 Kijani AI</span>
        <nav className="flex gap-4">
          <Link href="/pricing" className="text-sm hover:text-kijani-600">Pricing</Link>
          <Link href="/about" className="text-sm hover:text-kijani-600">About</Link>
          <Link href="/login"><Button variant="outline" size="sm">Login</Button></Link>
          <Link href="/register"><Button size="sm">Get Started</Button></Link>
        </nav>
      </header>

      <section className="mx-auto max-w-4xl px-8 py-24 text-center">
        <h1 className="text-5xl font-bold tracking-tight text-kijani-900">
          Agentic AI Sales for Tanzanian B2B
        </h1>
        <p className="mt-6 text-lg text-muted-foreground">
          Autonomous agents discover leads, research accounts, and engage via WhatsApp —
          in Swahili and English. Built for Tanzania.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link href="/register"><Button size="lg">Start Free Trial</Button></Link>
          <Link href="/pricing"><Button variant="outline" size="lg">View Pricing</Button></Link>
        </div>
      </section>

      <section className="bg-kijani-50 py-16">
        <div className="mx-auto grid max-w-5xl gap-8 px-8 md:grid-cols-3">
          {[
            { title: 'Scout', desc: 'Google Maps, Facebook, Instagram, BRELA lead discovery' },
            { title: 'Outreach', desc: 'WhatsApp-first with Swahili-English AI messages' },
            { title: 'Close', desc: 'Deal pipeline with local payment terms (LPO, 30/60/90 days)' },
          ].map((f) => (
            <div key={f.title} className="rounded-lg bg-white p-6 shadow-sm">
              <h3 className="font-semibold text-kijani-700">{f.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
