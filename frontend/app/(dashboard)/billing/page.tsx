'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PLAN_FEATURES } from '@/lib/constants';
import { useTenant } from '@/hooks/useTenant';
import { useUsage } from '@/hooks/useUsage';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import { useToast } from '@/components/ui/toast';
import type { PlanType } from '@/types';

export default function BillingPage() {
  const { tenant } = useTenant();
  const { data: usage } = useUsage();
  const token = useAuthStore((s) => s.accessToken);
  const { toast } = useToast();
  const [amount, setAmount] = useState('150000');
  const [phone, setPhone] = useState('');
  const [method, setMethod] = useState('m_pesa');

  const walletBalance = (tenant?.settings?.wallet_balance as number) ?? 0;

  const handleTopUp = async () => {
    await api.post(
      '/api/v1/billing/top-up',
      { amount: parseFloat(amount), payment_method: method, phone_number: phone },
      token || undefined
    );
    toast('M-Pesa push sent (demo) / Ombi la M-Pesa limetumwa', 'success');
  };

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold">Billing / Malipo</h1>
      <p className="text-muted-foreground">Plans in TZS — pay with M-Pesa, Tigo Pesa, or Airtel Money</p>

      {usage && (
        <Card className="mt-6">
          <CardContent className="pt-6 flex flex-wrap gap-6 text-sm">
            <div>
              <p className="text-muted-foreground">Leads used</p>
              <p className="text-xl font-bold">{usage.leads_used} / {usage.leads_limit}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Campaigns</p>
              <p className="text-xl font-bold">{usage.campaigns_used} / {usage.campaigns_limit}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Plan</p>
              <p className="text-xl font-bold capitalize">{usage.plan_type}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {(Object.keys(PLAN_FEATURES) as PlanType[]).map((plan) => (
          <Card key={plan} className={tenant?.plan_type === plan ? 'border-kijani-600' : ''}>
            <CardHeader>
              <CardTitle className="capitalize text-lg">{plan}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>{PLAN_FEATURES[plan].leads} leads</p>
              <p>{PLAN_FEATURES[plan].campaigns} campaigns</p>
              <p className="font-bold">
                {PLAN_FEATURES[plan].price === 0
                  ? 'Free'
                  : `TZS ${PLAN_FEATURES[plan].price.toLocaleString()}/mo`}
              </p>
              {tenant?.plan_type !== plan && plan !== 'enterprise' && (
                <Button variant="outline" size="sm" className="w-full" asChild>
                  <Link href="#">Upgrade (contact sales)</Link>
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Wallet / Mkoba — TZS {walletBalance.toLocaleString()}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input type="number" placeholder="Amount (TZS)" value={amount} onChange={(e) => setAmount(e.target.value)} />
          <Input placeholder="M-Pesa phone (+255...)" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="w-full rounded-md border px-3 py-2 text-sm"
          >
            <option value="m_pesa">M-Pesa</option>
            <option value="tigo_pesa">Tigo Pesa</option>
            <option value="airtel_money">Airtel Money</option>
          </select>
          <Button onClick={handleTopUp}>Pay with Mobile Money</Button>
          <p className="text-xs text-muted-foreground">MVP: mock payment. Production integrates Vodacom M-Pesa API.</p>
        </CardContent>
      </Card>
    </div>
  );
}
