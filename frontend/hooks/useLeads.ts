'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import type { Lead, PaginatedResponse, TargetCriteria } from '@/types';

export function useLeads(params?: {
  status?: string;
  search?: string;
  page?: number;
}) {
  const token = useAuthStore((s) => s.accessToken);
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.search) qs.set('search', params.search);
  if (params?.page) qs.set('page', String(params.page));

  return useQuery({
    queryKey: ['leads', params],
    queryFn: () =>
      api.get<PaginatedResponse<Lead>>(`/api/v1/leads?${qs}`, token || undefined),
    enabled: !!token,
  });
}

export function useLead(id: string) {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['lead', id],
    queryFn: () => api.get<Lead & Record<string, unknown>>(`/api/v1/leads/${id}`, token || undefined),
    enabled: !!token && !!id,
  });
}

export function useUpdateLead() {
  const token = useAuthStore((s) => s.accessToken);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      api.patch<Lead>(`/api/v1/leads/${id}`, data, token || undefined),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['leads'] });
      qc.invalidateQueries({ queryKey: ['lead', id] });
    },
  });
}

export function useDiscoverLeads() {
  const token = useAuthStore((s) => s.accessToken);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (criteria: TargetCriteria) =>
      api.post<{ job_id: string }>(
        '/api/v1/leads/discover',
        { target_criteria: criteria, auto_enrich: true },
        token || undefined
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['leads'] }),
  });
}
