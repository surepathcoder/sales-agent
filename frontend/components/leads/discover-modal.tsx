'use client';

import { useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SCRAPE_SOURCES } from '@/lib/constants';
import { useDiscoverLeads } from '@/hooks/useLeads';
import { useRealtime } from '@/hooks/useRealtime';
import { useToast } from '@/components/ui/toast';
import { DiscoveryProgress } from './discovery-progress';
import type { TargetCriteria } from '@/types';

interface DiscoverModalProps {
  open: boolean;
  onClose: () => void;
}

export function DiscoverModal({ open, onClose }: DiscoverModalProps) {
  const [query, setQuery] = useState('');
  const [locations, setLocations] = useState('Dar es Salaam, Arusha');
  const [sources, setSources] = useState<string[]>(['google_maps', 'web', 'facebook', 'instagram']);
  const [jobId, setJobId] = useState<string | null>(null);
  const discover = useDiscoverLeads();
  const qc = useQueryClient();
  const { toast } = useToast();

  const onComplete = useCallback(
    (data: { saved_count?: number; status: string }) => {
      qc.invalidateQueries({ queryKey: ['leads'] });
      if (data.status === 'completed' && (data.saved_count ?? 0) > 0) {
        toast(`${data.saved_count} leads discovered! / Wateja ${data.saved_count} wamepatikana`, 'success');
      }
    },
    [qc, toast]
  );

  const { update } = useRealtime(jobId || undefined, onComplete);

  if (!open) return null;

  const toggleSource = (id: string) => {
    setSources((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleDiscover = async () => {
    const criteria: TargetCriteria = {
      industries: query.split(',').map((s) => s.trim()).filter(Boolean),
      locations: locations.split(',').map((s) => s.trim()).filter(Boolean),
      company_sizes: [],
      min_lead_score: 0,
      max_results: 50,
      sources,
      search_query: query,
    };
    const result = await discover.mutateAsync(criteria);
    setJobId(result.job_id);
    toast('Scout agent started / Inatafuta wateja...', 'info');
  };

  const running = update?.status === 'running' || discover.isPending;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-xl font-semibold">Discover Leads / Tafuta Wateja</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Scout searches Google Maps, Facebook, Instagram & web for Tanzanian B2B businesses.
        </p>

        <div className="mt-4 space-y-4">
          <div>
            <label className="text-sm font-medium">Industry / Sekta</label>
            <Input
              placeholder="e.g. hardware stores, construction, duka la nguo"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="mt-1"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Locations / Mikoa</label>
            <Input value={locations} onChange={(e) => setLocations(e.target.value)} className="mt-1" />
          </div>
          <div>
            <label className="text-sm font-medium">Sources</label>
            <div className="mt-2 flex flex-wrap gap-2">
              {SCRAPE_SOURCES.map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => toggleSource(id)}
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    sources.includes(id)
                      ? 'bg-kijani-600 text-white'
                      : 'bg-kijani-100 text-kijani-800'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <DiscoveryProgress
          update={update}
          onViewLeads={() => {
            qc.invalidateQueries({ queryKey: ['leads'] });
            onClose();
          }}
        />

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={running}>
            {update?.status === 'completed' ? 'Close' : 'Cancel'}
          </Button>
          <Button onClick={handleDiscover} disabled={running || !query}>
            {running ? 'Discovering... / Inatafuta...' : 'Start Discovery'}
          </Button>
        </div>
      </div>
    </div>
  );
}
