'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreateDeal, useDeals } from '@/hooks/useDeals';

const STAGES = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost'];

export default function DealsPage() {
  const { data: deals = [], isLoading } = useDeals();
  const create = useCreateDeal();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ deal_name: '', value: '1000000', lead_id: '' });

  const handleCreate = async () => {
    if (!form.lead_id || !form.deal_name) return;
    await create.mutateAsync({
      lead_id: form.lead_id,
      deal_name: form.deal_name,
      value: parseFloat(form.value),
      currency: 'TZS',
    });
    setShowForm(false);
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Deals / Mikataba</h1>
          <p className="text-muted-foreground">Track opportunities from prospecting to close</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>New Deal</Button>
      </div>

      {showForm && (
        <Card className="mt-4">
          <CardContent className="grid gap-3 pt-6 md:grid-cols-3">
            <Input
              placeholder="Lead ID (from lead page URL)"
              value={form.lead_id}
              onChange={(e) => setForm({ ...form, lead_id: e.target.value })}
            />
            <Input
              placeholder="Deal name"
              value={form.deal_name}
              onChange={(e) => setForm({ ...form, deal_name: e.target.value })}
            />
            <Input
              type="number"
              placeholder="Value TZS"
              value={form.value}
              onChange={(e) => setForm({ ...form, value: e.target.value })}
            />
            <Button onClick={handleCreate} disabled={create.isPending}>
              Create
            </Button>
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <p className="mt-6">Loading...</p>
      ) : deals.length === 0 ? (
        <Card className="mt-6">
          <CardContent className="py-12 text-center text-muted-foreground">
            No deals yet. Create one from a qualified lead.
          </CardContent>
        </Card>
      ) : (
        <div className="mt-6 flex gap-4 overflow-x-auto pb-4">
          {STAGES.map((stage) => {
            const stageDeals = deals.filter((d) => d.stage === stage);
            return (
              <div key={stage} className="min-w-[260px]">
                <h3 className="mb-3 text-sm font-semibold capitalize">{stage.replace('_', ' ')}</h3>
                <div className="space-y-3">
                  {stageDeals.map((deal) => (
                    <Card key={deal.id}>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">{deal.deal_name}</CardTitle>
                      </CardHeader>
                      <CardContent className="text-sm">
                        <p>TZS {Number(deal.value).toLocaleString()}</p>
                        <p className="text-muted-foreground">{deal.probability}%</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
