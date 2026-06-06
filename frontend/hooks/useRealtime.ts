'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { API_URL } from '@/lib/constants';
import { useAuthStore } from '@/lib/auth';

export interface JobEvent {
  time: string;
  message: string;
  message_sw?: string;
}

export interface AgentJobUpdate {
  job_id: string;
  status: string;
  step?: string;
  progress_pct?: number;
  discovered_count?: number;
  saved_count?: number;
  total?: number;
  processed?: number;
  current_company?: string;
  last_saved_lead_id?: string;
  events?: JobEvent[];
  warning?: string;
  error?: string;
}

/**
 * Poll agent job progress every 1s for live lead discovery updates.
 */
export function useRealtime(jobId?: string, onComplete?: (data: AgentJobUpdate) => void) {
  const token = useAuthStore((s) => s.accessToken);
  const [update, setUpdate] = useState<AgentJobUpdate | null>(null);
  const [connected, setConnected] = useState(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const poll = useCallback(async () => {
    if (!jobId || !token) return null;
    const res = await fetch(`${API_URL}/api/v1/agents/job/${jobId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      return (await res.json()) as AgentJobUpdate;
    }
    return null;
  }, [jobId, token]);

  useEffect(() => {
    if (!jobId || !token) return;

    let cancelled = false;

    const run = async () => {
      try {
        const data = await poll();
        if (cancelled || !data) return;
        setUpdate(data);
        setConnected(true);
        if (data.status === 'completed' || data.status === 'failed') {
          onCompleteRef.current?.(data);
        }
      } catch {
        if (!cancelled) setConnected(false);
      }
    };

    run();
    const id = setInterval(run, 1000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [jobId, token, poll]);

  return { update, connected };
}
