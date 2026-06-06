'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import type { Tenant } from '@/types';

export function useTenant() {
  const tenant = useAuthStore((s) => s.tenant);
  const token = useAuthStore((s) => s.accessToken);

  const query = useQuery({
    queryKey: ['tenant', tenant?.id],
    queryFn: () => api.get<Tenant>('/api/v1/tenants/me', token || undefined),
    enabled: !!token,
    initialData: tenant || undefined,
  });

  return { tenant: query.data, isLoading: query.isLoading, refetch: query.refetch };
}
