'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useWhatsAppQr } from '@/hooks/useWhatsApp';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import { useToast } from '@/components/ui/toast';

const STEPS = [
  { id: 'welcome', title: 'Karibu!', titleEn: 'Welcome' },
  { id: 'market', title: 'Soko lako', titleEn: 'Your market' },
  { id: 'whatsapp', title: 'WhatsApp', titleEn: 'Connect WhatsApp' },
  { id: 'done', title: 'Tayari!', titleEn: 'Ready' },
];

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [industry, setIndustry] = useState('');
  const [locations, setLocations] = useState('Dar es Salaam');
  const token = useAuthStore((s) => s.accessToken);
  const router = useRouter();
  const { toast } = useToast();
  const { data: wa } = useWhatsAppQr();

  const finish = async () => {
    await api.patch(
      '/api/v1/tenants/me',
      {
        industry_vertical: industry || 'general',
        settings: {
          onboarding_complete: true,
          default_locations: locations.split(',').map((s) => s.trim()),
          whatsapp_status: wa?.status,
        },
      },
      token || undefined
    );
    toast('Setup complete! / Usanidi umekamilika', 'success');
    router.push('/dashboard');
  };

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-bold">Setup Kijani AI</h1>
      <p className="text-muted-foreground">Hatua {step + 1} ya {STEPS.length}</p>

      <div className="mt-4 flex gap-1">
        {STEPS.map((_, i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded ${i <= step ? 'bg-kijani-600' : 'bg-muted'}`}
          />
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{STEPS[step].title} — {STEPS[step].titleEn}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === 0 && (
            <p className="text-sm">
              Kijani AI helps Tanzanian businesses find B2B leads and reach them on WhatsApp
              with Swahili-English AI. Let&apos;s set up your account in 2 minutes.
            </p>
          )}
          {step === 1 && (
            <>
              <Input
                placeholder="Your industry e.g. hardware, construction, FMCG"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
              />
              <Input
                placeholder="Target cities (comma-separated)"
                value={locations}
                onChange={(e) => setLocations(e.target.value)}
              />
            </>
          )}
          {step === 2 && (
            <div className="text-center">
              <p className="mb-4 text-sm text-muted-foreground">
                Scan QR with WhatsApp on your phone (Linked Devices)
              </p>
              {wa?.qr ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={wa.qr} alt="WhatsApp QR" className="mx-auto h-48 w-48" />
              ) : (
                <p className="text-sm">Status: {wa?.status ?? 'loading...'}</p>
              )}
              <p className="mt-2 text-xs text-muted-foreground">You can skip and connect later in Settings</p>
            </div>
          )}
          {step === 3 && (
            <ul className="space-y-2 text-sm">
              <li>✓ Account created</li>
              <li>✓ Market: {industry || 'general'} in {locations}</li>
              <li>✓ WhatsApp: {wa?.status === 'connected' ? 'Connected' : 'Setup later'}</li>
              <li className="font-medium text-kijani-700">Next: Discover your first leads!</li>
            </ul>
          )}
        </CardContent>
      </Card>

      <div className="mt-6 flex justify-between">
        <Button variant="outline" disabled={step === 0} onClick={() => setStep(step - 1)}>
          Back
        </Button>
        {step < STEPS.length - 1 ? (
          <Button onClick={() => setStep(step + 1)}>Next</Button>
        ) : (
          <Button onClick={finish}>Go to Dashboard</Button>
        )}
      </div>
    </div>
  );
}
