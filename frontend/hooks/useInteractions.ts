'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

export interface Interaction {
  id: string;
  lead_id: string;
  contact_id: string;
  channel: string;
  direction: string;
  content: string;
  ai_generated: boolean;
  human_approved: boolean | null;
  created_at: string;
}

export function useLeadInteractions(leadId: string) {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['interactions', leadId],
    queryFn: () =>
      api.get<Interaction[]>(`/api/v1/interactions/lead/${leadId}`, token || undefined),
    enabled: !!token && !!leadId,
  });
}

export function usePendingOutreach() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['pending-outreach'],
    queryFn: () => api.get<Interaction[]>('/api/v1/interactions/pending', token || undefined),
    enabled: !!token,
  });
}

export function useApproveOutreach() {
  const token = useAuthStore((s) => s.accessToken);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (interactionId: string) =>
      api.post<Interaction>(
        `/api/v1/interactions/${interactionId}/approve`,
        { send_now: true },
        token || undefined
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pending-outreach'] });
      qc.invalidateQueries({ queryKey: ['interactions'] });
    },
  });
}
