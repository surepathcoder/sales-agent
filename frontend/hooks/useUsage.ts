'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

export interface Usage {
  plan_type: string;
  leads_used: number;
  leads_limit: number;
  campaigns_used: number;
  campaigns_limit: number;
  leads_remaining: number;
  campaigns_remaining: number;
  onboarding_complete: boolean;
  whatsapp_connected: boolean;
}

export function useUsage() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['usage'],
    queryFn: () => api.get<Usage>('/api/v1/usage', token || undefined),
    enabled: !!token,
    refetchInterval: 60000,
  });
}
