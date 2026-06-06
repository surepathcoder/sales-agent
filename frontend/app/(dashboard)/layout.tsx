'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Sidebar } from '@/components/dashboard/sidebar';
import { Topbar } from '@/components/dashboard/topbar';
import { PlanBanner } from '@/components/dashboard/plan-banner';
import { useAuthStore } from '@/lib/auth';
import { useUsage } from '@/hooks/useUsage';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const token = useAuthStore((s) => s.accessToken);
  const { data: usage } = useUsage();

  useEffect(() => {
    if (!token) router.replace('/login');
  }, [token, router]);

  useEffect(() => {
    if (
      usage &&
      !usage.onboarding_complete &&
      pathname !== '/onboarding' &&
      token
    ) {
      router.replace('/onboarding');
    }
  }, [usage, pathname, router, token]);

  if (!token) return null;

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <PlanBanner />
        <main className="flex-1 overflow-auto bg-muted/30 p-6">{children}</main>
      </div>
    </div>
  );
}
