'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useWhatsAppQr, useWhatsAppStatus } from '@/hooks/useWhatsApp';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import { useToast } from '@/components/ui/toast';

export default function SettingsPage() {
  const token = useAuthStore((s) => s.accessToken);
  const { data: status } = useWhatsAppStatus();
  const { data: qrData, refetch: refreshQr } = useWhatsAppQr();
  const { toast } = useToast();
  const qc = useQueryClient();

  const [showAddForm, setShowAddForm] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('agent');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data: team = [] } = useQuery({
    queryKey: ['team'],
    queryFn: () =>
      api.get<Array<{ id: string; email: string; role: string; phone: string }>>(
        '/api/v1/users',
        token || undefined
      ),
    enabled: !!token,
  });

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail || !newPhone || !newPassword) return;
    setIsSubmitting(true);
    try {
      await api.post(
        '/api/v1/users',
        { email: newEmail, phone: newPhone, password: newPassword, role: newRole },
        token || undefined
      );
      toast('Team member added successfully! / Mwanachama ameongezwa.', 'success');
      setNewEmail('');
      setNewPhone('');
      setNewPassword('');
      setNewRole('agent');
      setShowAddForm(false);
      qc.invalidateQueries({ queryKey: ['team'] });
    } catch (err: any) {
      toast(err.message || 'Failed to add member', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings / Mipangilio</h1>
        <p className="text-muted-foreground">WhatsApp, team, and preferences</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>WhatsApp Connection</span>
            {status?.status === 'connected' ? (
              <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800">
                Connected
              </span>
            ) : status?.status === 'initializing' ? (
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800 animate-pulse">
                Initializing...
              </span>
            ) : status?.status === 'offline' ? (
              <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-800">
                Offline
              </span>
            ) : (
              <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-800">
                {status?.status || 'Offline / Error'}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Connect Kijani AI to your WhatsApp business or personal account to send automated outreach messages.
          </p>

          {status?.status === 'connected' ? (
            <div className="rounded-lg bg-green-50/50 border border-green-200 p-4">
              <p className="text-sm text-green-800 font-medium flex items-center gap-2">
                ✓ WhatsApp connected — ready for outreach / Tayari kwa kazi
              </p>
            </div>
          ) : (
            <>
              <div className="rounded-md bg-muted p-4 text-sm text-muted-foreground space-y-1">
                <p className="font-semibold text-foreground mb-1">Usanidi / Connection Steps:</p>
                <ol className="list-decimal space-y-1 pl-4">
                  <li>Fungua WhatsApp kwenye simu yako (Open WhatsApp)</li>
                  <li>Mipangilio → Vifaa Vilivyounganishwa (Linked Devices → Link a Device)</li>
                  <li>Skena msimbo wa QR hapa chini (Scan the QR code below)</li>
                </ol>
              </div>

              {status?.status === 'offline' && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-800">
                  Kijani WhatsApp service is offline. Please make sure Docker or the local sidecar service is started.
                </div>
              )}

              <div className="flex flex-col items-center justify-center p-6 border rounded-lg bg-muted/20 relative min-h-[250px]">
                {qrData?.qr && status?.status !== 'connected' && status?.status !== 'offline' ? (
                  <div className="space-y-3 text-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={qrData.qr} alt="WhatsApp QR" className="mx-auto h-48 w-48 border rounded-lg bg-white p-2 shadow-sm" />
                    <p className="text-xs text-muted-foreground">Msimbo huu utajisasisha kiotomatiki (Auto-refreshes)</p>
                  </div>
                ) : status?.status === 'initializing' ? (
                  <div className="text-center space-y-2">
                    <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-kijani-600 border-t-transparent" />
                    <p className="text-sm text-muted-foreground font-medium">Inafungua WhatsApp Web... / Booting browser...</p>
                    <p className="text-xs text-muted-foreground max-w-[280px]">Inaweza kuchukua sekunde 15 hadi 30. (Takes 15-30 seconds)</p>
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground space-y-1">
                    <p className="text-sm font-semibold">QR code unavailable</p>
                    <p className="text-xs max-w-xs">Tafadhali bonyeza &quot;Refresh QR&quot; au hakikisha huduma ya WhatsApp inaendeshwa.</p>
                  </div>
                )}
              </div>
            </>
          )}

          <Button
            variant="outline"
            className="w-full sm:w-auto"
            onClick={() => refreshQr()}
            disabled={status?.status === 'connected' || status?.status === 'offline'}
          >
            Mpye Msimbo / Refresh QR
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Team / Timu</CardTitle>
          <Button size="sm" onClick={() => setShowAddForm(!showAddForm)}>
            {showAddForm ? 'Funga / Close' : 'Ongeza / Add Member'}
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {showAddForm && (
            <form onSubmit={handleAddMember} className="space-y-3 border rounded-lg p-4 bg-muted/20">
              <p className="text-sm font-semibold text-kijani-950">Ongeza Mwanachama / Add Team Member</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <Input
                  type="email"
                  placeholder="Email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  required
                />
                <Input
                  type="text"
                  placeholder="Simu (e.g. +255...)"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  required
                />
                <Input
                  type="password"
                  placeholder="Password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
                <select
                  className="rounded border bg-white px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-kijani-600"
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                >
                  <option value="owner">Owner / Mmiliki</option>
                  <option value="manager">Manager / Meneja</option>
                  <option value="agent">Agent / Muuzaji</option>
                  <option value="viewer">Viewer / Mtazamaji</option>
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={isSubmitting}>
                  {isSubmitting ? 'Inahifadhi...' : 'Save Member'}
                </Button>
              </div>
            </form>
          )}

          <div className="space-y-2">
            {team.map((m) => (
              <div key={m.id} className="flex justify-between rounded border px-3 py-2 text-sm items-center">
                <div className="flex flex-col">
                  <span>{m.email}</span>
                  <span className="text-xs text-muted-foreground">{m.phone}</span>
                </div>
                <span className="rounded-full bg-kijani-100 px-3 py-1 text-xs font-semibold text-kijani-800 capitalize">
                  {m.role.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
