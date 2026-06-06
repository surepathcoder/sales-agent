'use client';

import { useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCampaignAnalytics, useStartCampaign } from '@/hooks/useCampaigns';

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: analytics, isLoading } = useCampaignAnalytics(id);
  const start = useStartCampaign();

  const funnel = analytics?.funnel ?? {};

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campaign Analytics</h1>
          <p className="text-muted-foreground">Campaign ID: {id}</p>
        </div>
        <Button onClick={() => start.mutate(id)} disabled={start.isPending}>
          {start.isPending ? 'Starting...' : 'Start / Run Outreach'}
        </Button>
      </div>

      {isLoading ? (
        <p className="mt-6">Loading...</p>
      ) : (
        <>
          <div className="mt-6 grid gap-4 md:grid-cols-4">
            {['total', 'contacted', 'engaged', 'converted'].map((key) => (
              <Card key={key}>
                <CardContent className="pt-6">
                  <p className="text-sm text-muted-foreground capitalize">{key}</p>
                  <p className="text-2xl font-bold">{funnel[key] ?? '—'}</p>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card className="mt-6">
            <CardHeader><CardTitle>Performance</CardTitle></CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>Cost per lead: TZS {Number(analytics?.cost_per_lead ?? 0).toLocaleString()}</p>
              <p>ROI estimate: {analytics?.roi != null ? `${analytics.roi}%` : '—'}</p>
              <p>WhatsApp: {analytics?.channel_performance?.whatsapp ?? 0}</p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
