'use client';

import { useParams } from 'next/navigation';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useLeadInteractions } from '@/hooks/useInteractions';
import { useLead } from '@/hooks/useLeads';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import { useQuery } from '@tanstack/react-query';
import type { Lead } from '@/types';

const TABS = ['Overview', 'Contacts', 'Interactions', 'Deals', 'Agent Memory', 'AI Insights'];

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: lead, isLoading } = useLead(id);
  const { data: interactions = [] } = useLeadInteractions(id);
  const token = useAuthStore((s) => s.accessToken);
  const [tab, setTab] = useState('Overview');

  const { data: memories = [] } = useQuery({
    queryKey: ['agent-memory', id],
    queryFn: () =>
      api.get<Array<{ id: string; agent_type: string; content: string; confidence_score: number }>>(
        `/api/v1/agents/memory/${id}`,
        token || undefined
      ),
    enabled: !!token && !!id && tab === 'Agent Memory',
  });

  if (isLoading) return <p>Loading...</p>;
  if (!lead) return <p>Lead not found</p>;

  const dossier = lead as Lead & {
    contacts?: Array<Record<string, string>>;
    deals?: Array<Record<string, unknown>>;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{lead.company_name}</h1>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-kijani-100 px-3 py-1 text-xs font-medium capitalize">
              {lead.status.replace('_', ' ')}
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs">Score: {lead.lead_score}</span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs capitalize">{lead.priority}</span>
          </div>
        </div>
        <Button
          variant="outline"
          className="w-full sm:w-auto"
          onClick={() =>
            api.post(
              '/api/v1/agents/trigger/outreach',
              { lead_id: id },
              token || undefined
            )
          }
        >
          Run Outreach Agent
        </Button>
      </div>

      <div className="flex gap-2 border-b overflow-x-auto pb-px whitespace-nowrap scrollbar-none">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium flex-shrink-0 transition-colors ${
              tab === t
                ? 'border-b-2 border-kijani-600 text-kijani-700'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {tab === 'Overview' && (
          <Card>
            <CardHeader><CardTitle>Company Info</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p><strong>Source:</strong> {lead.source}</p>
              <p><strong>Address:</strong> {lead.address || '—'}</p>
              <p><strong>Tags:</strong> {lead.tags?.join(', ') || '—'}</p>
              <p><strong>Contacts:</strong> {lead.contact_count}</p>
            </CardContent>
          </Card>
        )}
        {tab === 'Contacts' && (
          <Card>
            <CardContent className="pt-6 space-y-3">
              {(dossier.contacts || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No contacts yet.</p>
              ) : (
                dossier.contacts!.map((c) => (
                  <div key={c.id} className="rounded border p-3 text-sm">
                    <p className="font-medium">{c.first_name} {c.last_name}</p>
                    <p>WhatsApp: {c.whatsapp_number}</p>
                    {c.email && <p>Email: {c.email}</p>}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        )}
        {tab === 'Interactions' && (
          <Card>
            <CardContent className="pt-6 space-y-3">
              {interactions.length === 0 ? (
                <p className="text-sm text-muted-foreground">No interactions yet.</p>
              ) : (
                interactions.map((i) => (
                  <div key={i.id} className="rounded border p-3 text-sm">
                    <p className="text-xs text-muted-foreground capitalize">
                      {i.direction} · {i.channel} · {new Date(i.created_at).toLocaleString()}
                    </p>
                    <p className="mt-1">{i.content}</p>
                    {i.human_approved === null && i.ai_generated && (
                      <span className="mt-1 inline-block text-xs text-amber-600">Pending approval</span>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        )}
        {tab === 'Deals' && (
          <Card>
            <CardContent className="pt-6 space-y-3">
              {(dossier.deals || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No deals linked.</p>
              ) : (
                dossier.deals!.map((d) => (
                  <div key={String(d.id)} className="rounded border p-3 text-sm">
                    <p className="font-medium">{String(d.deal_name)}</p>
                    <p>Stage: {String(d.stage)} · {String(d.probability)}%</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        )}
        {tab === 'AI Insights' && (
          <Card>
            <CardContent className="pt-6">
              <pre className="text-sm overflow-auto">{JSON.stringify(lead.ai_insights, null, 2)}</pre>
            </CardContent>
          </Card>
        )}
        {tab === 'Agent Memory' && (
          <Card>
            <CardContent className="pt-6 space-y-3">
              {memories.length === 0 ? (
                <p className="text-sm text-muted-foreground">No agent memories yet.</p>
              ) : (
                memories.map((m) => (
                  <div key={m.id} className="rounded border p-3 text-sm">
                    <p className="text-xs text-muted-foreground">{m.agent_type}</p>
                    <p className="mt-1">{m.content}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
