'use client';

import { useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { DiscoveryProgress } from '@/components/leads/discovery-progress';
import { SCRAPE_SOURCES } from '@/lib/constants';
import { useDiscoverLeads } from '@/hooks/useLeads';
import { useRealtime } from '@/hooks/useRealtime';
import { useToast } from '@/components/ui/toast';

export default function DiscoverPage() {
  const [query, setQuery] = useState('');
  const [sources, setSources] = useState(['google_maps', 'web', 'facebook', 'instagram']);
  const [jobId, setJobId] = useState<string | null>(null);
  const discover = useDiscoverLeads();
  const qc = useQueryClient();
  const router = useRouter();
  const { toast } = useToast();

  const onComplete = useCallback(
    (data: { saved_count?: number }) => {
      qc.invalidateQueries({ queryKey: ['leads'] });
      if ((data.saved_count ?? 0) > 0) {
        toast(`${data.saved_count} leads ready!`, 'success');
      }
    },
    [qc, toast]
  );

  const { update } = useRealtime(jobId || undefined, onComplete);

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold">Discover Leads / Tafuta Wateja</h1>
      <p className="text-muted-foreground">
        Scout agent searches Google Maps, Facebook, Instagram, and web.
      </p>

      <div className="mt-6 space-y-4">
        <Input placeholder="Search query / e.g. hardware stores DSM" value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          {SCRAPE_SOURCES.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() =>
                setSources((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
              }
              className={`rounded-full px-3 py-1 text-xs ${
                sources.includes(id) ? 'bg-kijani-600 text-white' : 'bg-muted'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <Button
          onClick={async () => {
            const r = await discover.mutateAsync({
              industries: [query],
              locations: ['Dar es Salaam, Tanzania'],
              company_sizes: [],
              min_lead_score: 0,
              max_results: 50,
              sources,
              search_query: query,
            });
            setJobId(r.job_id);
          }}
          disabled={!query || discover.isPending || update?.status === 'running'}
        >
          {update?.status === 'running' ? 'Discovering...' : 'Start Discovery'}
        </Button>

        <DiscoveryProgress
          update={update}
          onViewLeads={() => {
            qc.invalidateQueries({ queryKey: ['leads'] });
            router.push('/leads');
          }}
        />
      </div>
    </div>
  );
}
