'use client';

import { useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { DiscoverModal } from '@/components/leads/discover-modal';
import { KanbanBoard } from '@/components/leads/kanban-board';
import { LeadCard } from '@/components/leads/lead-card';
import { useLeads } from '@/hooks/useLeads';
import { useToast } from '@/components/ui/toast';
import { API_URL } from '@/lib/constants';
import { useAuthStore } from '@/lib/auth';

export default function LeadsPage() {
  const [view, setView] = useState<'kanban' | 'list'>('kanban');
  const [search, setSearch] = useState('');
  const [discoverOpen, setDiscoverOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const { data, isLoading } = useLeads({ search: search || undefined });
  const qc = useQueryClient();
  const { toast } = useToast();
  const token = useAuthStore((s) => s.accessToken);

  const leads = data?.items ?? [];

  const handleImport = async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_URL}/api/v1/leads/import`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const result = await res.json();
    if (res.ok) {
      toast(`Imported ${result.imported} leads (${result.skipped} skipped)`, 'success');
      qc.invalidateQueries({ queryKey: ['leads'] });
    } else {
      toast('Import failed', 'error');
    }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Leads / Wateja</h1>
          <p className="text-muted-foreground">{data?.total ?? 0} total leads</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleImport(e.target.files[0])}
          />
          <Button variant="outline" onClick={() => fileRef.current?.click()}>
            Import CSV
          </Button>
          <Button variant="outline" onClick={() => setView(view === 'kanban' ? 'list' : 'kanban')}>
            {view === 'kanban' ? 'List' : 'Kanban'}
          </Button>
          <Button onClick={() => setDiscoverOpen(true)}>Discover Leads</Button>
        </div>
      </div>

      <div className="mt-4">
        <Input
          placeholder="Search companies... / Tafuta kampuni"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="mt-6">
        {isLoading ? (
          <p>Loading...</p>
        ) : leads.length === 0 ? (
          <div className="rounded-lg border border-dashed p-12 text-center">
            <p className="text-muted-foreground">No leads yet / Hakuna wateja bado</p>
            <Button className="mt-4" onClick={() => setDiscoverOpen(true)}>
              Discover your first leads
            </Button>
          </div>
        ) : view === 'kanban' ? (
          <KanbanBoard leads={leads} />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {leads.map((lead) => (
              <LeadCard key={lead.id} lead={lead} />
            ))}
          </div>
        )}
      </div>

      <DiscoverModal open={discoverOpen} onClose={() => setDiscoverOpen(false)} />
    </div>
  );
}
