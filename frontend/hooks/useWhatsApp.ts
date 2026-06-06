'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

export function useWhatsAppStatus() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['whatsapp-status'],
    queryFn: () =>
      api.get<{ tenant_id: string; status: string; qr?: string | null }>(
        '/api/v1/integrations/whatsapp/status',
        token || undefined
      ),
    enabled: !!token,
    refetchInterval: 5000,
  });
}

export function useWhatsAppQr() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['whatsapp-qr'],
    queryFn: () =>
      api.get<{ tenant_id: string; status: string; qr: string | null }>(
        '/api/v1/integrations/whatsapp/qr',
        token || undefined
      ),
    enabled: !!token,
    refetchInterval: 10000,
  });
}
