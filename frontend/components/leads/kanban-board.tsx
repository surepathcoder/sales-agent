'use client';

import type { Lead, LeadStatus } from '@/types';
import { LEAD_STATUSES } from '@/lib/constants';
import { useUpdateLead } from '@/hooks/useLeads';
import { LeadCard } from './lead-card';

export function KanbanBoard({ leads }: { leads: Lead[] }) {
  const updateLead = useUpdateLead();
  const columns = LEAD_STATUSES.filter((s) => !['nurture'].includes(s));

  const handleStatusChange = (leadId: string, status: LeadStatus) => {
    updateLead.mutate({ id: leadId, data: { status } });
  };

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map((status) => {
        const columnLeads = leads.filter((l) => l.status === status);
        return (
          <div key={status} className="min-w-[280px] flex-shrink-0">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold capitalize">{status.replace('_', ' ')}</h3>
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs">{columnLeads.length}</span>
            </div>
            <div className="space-y-3">
              {columnLeads.map((lead) => (
                <div key={lead.id} className="space-y-2">
                  <LeadCard lead={lead} />
                  <select
                    className="w-full rounded border px-2 py-1 text-xs"
                    value={lead.status}
                    onChange={(e) => handleStatusChange(lead.id, e.target.value as LeadStatus)}
                  >
                    {columns.map((s) => (
                      <option key={s} value={s}>
                        {s.replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
