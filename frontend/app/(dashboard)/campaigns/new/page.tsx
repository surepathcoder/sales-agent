'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCreateCampaign } from '@/hooks/useCampaigns';
import { useLeads } from '@/hooks/useLeads';

const STEPS = ['Target Criteria', 'Agent Config', 'Select Leads', 'Review'];

export default function NewCampaignPage() {
  const [step, setStep] = useState(0);
  const [name, setName] = useState('');
  const [swahiliRatio, setSwahiliRatio] = useState(0.5);
  const [selectedLeads, setSelectedLeads] = useState<string[]>([]);
  const create = useCreateCampaign();
  const { data: leadsData } = useLeads({ page: 1 });
  const router = useRouter();
  const leads = leadsData?.items ?? [];

  const toggleLead = (id: string) => {
    setSelectedLeads((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleCreate = async () => {
    await create.mutateAsync({
      name,
      campaign_type: 'outbound_sequence',
      target_criteria: { industries: [], locations: ['Dar es Salaam'] },
      lead_pool: selectedLeads,
      agent_configuration: {
        tone: 'professional',
        swahili_ratio: swahiliRatio,
        human_approval_required: true,
        max_daily_outreach: 50,
      },
      sequence_steps: [
        { step_order: 1, channel: 'whatsapp', delay_hours: 0, template_id: 'intro' },
        { step_order: 2, channel: 'whatsapp', delay_hours: 48, template_id: 'followup' },
      ],
    });
    router.push('/campaigns');
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold">Campaign Builder</h1>
      <div className="mt-4 flex gap-2">
        {STEPS.map((s, i) => (
          <span
            key={s}
            className={`rounded-full px-3 py-1 text-xs ${
              i === step ? 'bg-kijani-600 text-white' : 'bg-muted'
            }`}
          >
            {i + 1}. {s}
          </span>
        ))}
      </div>

      <div className="mt-6 space-y-4">
        {step === 0 && (
          <Input placeholder="Campaign name" value={name} onChange={(e) => setName(e.target.value)} />
        )}
        {step === 1 && (
          <div>
            <label className="text-sm">Swahili ratio: {swahiliRatio}</label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={swahiliRatio}
              onChange={(e) => setSwahiliRatio(parseFloat(e.target.value))}
              className="mt-2 w-full"
            />
          </div>
        )}
        {step === 2 && (
          <div className="max-h-64 space-y-2 overflow-y-auto">
            {leads.length === 0 ? (
              <p className="text-sm text-muted-foreground">No leads — discover leads first.</p>
            ) : (
              leads.map((lead) => (
                <label key={lead.id} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedLeads.includes(lead.id)}
                    onChange={() => toggleLead(lead.id)}
                  />
                  {lead.company_name} (score: {lead.lead_score})
                </label>
              ))
            )}
          </div>
        )}
        {step === 3 && (
          <p className="text-sm">
            Launch &quot;{name}&quot; with {selectedLeads.length} leads
          </p>
        )}
      </div>

      <div className="mt-6 flex gap-2">
        {step > 0 && <Button variant="outline" onClick={() => setStep(step - 1)}>Back</Button>}
        {step < STEPS.length - 1 ? (
          <Button onClick={() => setStep(step + 1)} disabled={step === 0 && !name}>
            Next
          </Button>
        ) : (
          <Button onClick={handleCreate} disabled={!name || create.isPending}>
            Launch Campaign
          </Button>
        )}
      </div>
    </div>
  );
}
