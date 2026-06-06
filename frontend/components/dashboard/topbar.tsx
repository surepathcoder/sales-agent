'use client';

import { useAuthStore } from '@/lib/auth';
import { Button } from '@/components/ui/button';

export function Topbar() {
  const { user, tenant, logout } = useAuthStore();

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div>
        <p className="text-sm text-muted-foreground">Tenant</p>
        <p className="font-medium">{tenant?.name || '—'}</p>
      </div>
      <div className="flex items-center gap-4">
        <span className="rounded-full bg-kijani-100 px-3 py-1 text-xs font-medium text-kijani-700">
          {tenant?.plan_type?.toUpperCase()}
        </span>
        <span className="text-sm">{user?.email}</span>
        <Button variant="outline" size="sm" onClick={logout}>
          Logout
        </Button>
      </div>
    </header>
  );
}
