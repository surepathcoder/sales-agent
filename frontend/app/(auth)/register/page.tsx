'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PLAN_FEATURES } from '@/lib/constants';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import type { PlanType, Tenant, User } from '@/types';

export default function RegisterPage() {
  const [form, setForm] = useState({
    company_name: '',
    email: '',
    phone: '',
    password: '',
    industry_vertical: 'general',
    plan_type: 'free' as PlanType,
  });
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await api.post<{
        access_token: string;
        refresh_token: string;
        user: User;
        tenant: Tenant;
      }>('/api/v1/auth/register', form);
      setAuth(data);
      router.push('/onboarding');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-center">Create Account</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input placeholder="Company name" value={form.company_name} onChange={(e) => setForm({ ...form, company_name: e.target.value })} required />
          <Input type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <Input placeholder="Phone (+255...)" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <Input type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <Input placeholder="Industry" value={form.industry_vertical} onChange={(e) => setForm({ ...form, industry_vertical: e.target.value })} />

          <div className="grid grid-cols-2 gap-2">
            {(Object.keys(PLAN_FEATURES) as PlanType[]).map((plan) => (
              <button
                key={plan}
                type="button"
                onClick={() => setForm({ ...form, plan_type: plan })}
                className={`rounded-lg border p-3 text-left text-xs ${
                  form.plan_type === plan ? 'border-kijani-600 bg-kijani-50' : ''
                }`}
              >
                <strong className="capitalize">{plan}</strong>
                <p>{PLAN_FEATURES[plan].leads} leads</p>
              </button>
            ))}
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Creating...' : 'Register'}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm">
          Have an account? <Link href="/login" className="text-kijani-600">Sign in</Link>
        </p>
      </CardContent>
    </Card>
  );
}
