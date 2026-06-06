'use client';

import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useWhatsAppQr, useWhatsAppStatus } from '@/hooks/useWhatsApp';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

export default function SettingsPage() {
  const token = useAuthStore((s) => s.accessToken);
  const { data: status } = useWhatsAppStatus();
  const { data: qrData, refetch: refreshQr } = useWhatsAppQr();

  const { data: team = [] } = useQuery({
    queryKey: ['team'],
    queryFn: () =>
      api.get<Array<{ id: string; email: string; role: string; phone: string }>>(
        '/api/v1/users',
        token || undefined
      ),
    enabled: !!token,
  });

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings / Mipangilio</h1>
        <p className="text-muted-foreground">WhatsApp, team, and preferences</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>WhatsApp Connection</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm">
            Status: <strong className="capitalize">{status?.status || 'unknown'}</strong>
          </p>
          {status?.status !== 'connected' && (
            <div className="rounded-md bg-muted p-4 text-sm">
              <ol className="list-decimal space-y-1 pl-4">
                <li>Open WhatsApp on your phone</li>
                <li>Settings → Linked Devices → Link a Device</li>
                <li>Scan the QR code below</li>
              </ol>
            </div>
          )}
          {qrData?.qr && status?.status !== 'connected' && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={qrData.qr} alt="WhatsApp QR" className="mx-auto h-64 w-64" />
          )}
          {status?.status === 'connected' && (
            <p className="text-sm text-green-700">✓ WhatsApp connected — ready for outreach</p>
          )}
          <Button variant="outline" onClick={() => refreshQr()}>
            Refresh QR
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Team / Timu</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {team.map((m) => (
            <div key={m.id} className="flex justify-between rounded border px-3 py-2 text-sm">
              <span>{m.email}</span>
              <span className="capitalize text-muted-foreground">{m.role.replace('_', ' ')}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
