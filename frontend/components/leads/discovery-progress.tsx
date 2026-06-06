'use client';

import { Button } from '@/components/ui/button';
import type { AgentJobUpdate } from '@/hooks/useRealtime';

interface DiscoveryProgressProps {
  update: AgentJobUpdate | null;
  onViewLeads?: () => void;
}

const STEP_LABELS: Record<string, { en: string; sw: string }> = {
  starting: { en: 'Starting...', sw: 'Inaanza...' },
  scouting: { en: 'Searching sources', sw: 'Inatafuta vyanzo' },
  found: { en: 'Candidates found', sw: 'Wateja wamepatikana' },
  saving: { en: 'Saving leads', sw: 'Inahifadhi wateja' },
  enriching: { en: 'AI research', sw: 'Uchambuzi wa AI' },
};

export function DiscoveryProgress({ update, onViewLeads }: DiscoveryProgressProps) {
  if (!update) return null;

  const pct = update.progress_pct ?? (update.status === 'completed' ? 100 : update.status === 'running' ? 30 : 0);
  const step = update.step ? STEP_LABELS[update.step] : null;
  const isDone = update.status === 'completed';
  const isFailed = update.status === 'failed';

  return (
    <div className="mt-4 space-y-3 rounded-lg border border-kijani-200 bg-kijani-50/50 p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium capitalize">
          {isDone ? '✓ Complete / Imekamilika' : isFailed ? '✗ Failed / Imeshindwa' : step?.sw ?? update.status}
        </span>
        <span className="text-muted-foreground">{pct}%</span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-kijani-600 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>

      {(update.saved_count != null || update.discovered_count != null) && (
        <p className="text-sm text-kijani-800">
          {update.saved_count ?? 0} saved
          {update.discovered_count != null && ` / ${update.discovered_count} found`}
          {update.current_company && ` — ${update.current_company}`}
        </p>
      )}

      {update.events && update.events.length > 0 && (
        <ul className="max-h-32 space-y-1 overflow-y-auto text-xs text-muted-foreground">
          {update.events.slice(-8).map((e, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-kijani-600">•</span>
              <span>{e.message_sw || e.message}</span>
            </li>
          ))}
        </ul>
      )}

      {update.warning && <p className="text-sm text-amber-700">{update.warning}</p>}
      {update.error && <p className="text-sm text-red-600">{update.error}</p>}

      {isDone && update.saved_count != null && update.saved_count > 0 && onViewLeads && (
        <Button size="sm" className="w-full" onClick={onViewLeads}>
          View {update.saved_count} new leads / Angalia wateja
        </Button>
      )}
    </div>
  );
}
