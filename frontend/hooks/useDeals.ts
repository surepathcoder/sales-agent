'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

export interface Deal {
  id: string;
  lead_id: string;
  deal_name: string;
  value: number;
  currency: string;
  stage: string;
  probability: number;
  expected_close_date: string;
  created_at: string;
}

export function useDeals() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['deals'],
    queryFn: () => api.get<Deal[]>('/api/v1/deals', token || undefined),
    enabled: !!token,
  });
}

export function useCreateDeal() {
  const token = useAuthStore((s) => s.accessToken);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post<Deal>('/api/v1/deals', data, token || undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  });
}

export function useUpdateDeal() {
  const token = useAuthStore((s) => s.accessToken);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      api.patch<Deal>(`/api/v1/deals/${id}`, data, token || undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  });
}
