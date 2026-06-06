import Link from 'next/link';
import type { Lead } from '@/types';
import { cn } from '@/lib/utils';

const priorityColors = {
  hot: 'bg-red-100 text-red-700',
  warm: 'bg-amber-100 text-amber-700',
  cold: 'bg-blue-100 text-blue-700',
};

export function LeadCard({ lead }: { lead: Lead }) {
  return (
    <Link
      href={`/leads/${lead.id}`}
      className="block rounded-lg border bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium">{lead.company_name}</h3>
          <p className="text-xs text-muted-foreground capitalize">{lead.status.replace('_', ' ')}</p>
        </div>
        <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', priorityColors[lead.priority])}>
          {lead.priority}
        </span>
      </div>
      <div className="mt-3 flex items-center justify-between text-sm">
        <span>Score: {lead.lead_score}</span>
        <span className="text-muted-foreground">{lead.contact_count} contacts</span>
      </div>
    </Link>
  );
}
