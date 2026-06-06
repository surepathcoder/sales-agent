'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import type { Campaign } from '@/types';

export function useCampaigns() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['campaigns'],
    queryFn: () => api.get<Campaign[]>('/api/v1/campaigns', token || undefined),
    enabled: !!token,
  });
}

export function useCampaignAnalytics(id: string) {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['campaign-analytics', id],
    queryFn: () =>
      api.get<{
        funnel: Record<string, number>;
        channel_performance: Record<string, number>;
        cost_per_lead: number;
        roi: number | null;
      }>(`/api/v1/campaigns/${id}/analytics`, token || undefined),
    enabled: !!token && !!id,
  });
}

export function useCreateCampaign() {
  const token = useAuthStore((s) => s.accessToken);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post<Campaign>('/api/v1/campaigns', data, token || undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }),
  });
}

export function useStartCampaign() {
  const token = useAuthStore((s) => s.accessToken);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post<Campaign>(`/api/v1/campaigns/${id}/start`, {}, token || undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }),
  });
}
