'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

export default function AnalyticsPage() {
  const token = useAuthStore((s) => s.accessToken);
  const { data } = useQuery({
    queryKey: ['analytics-full'],
    queryFn: () =>
      api.get<{
        total_leads: number;
        conversion_rate: number;
        avg_deal_value: number;
        active_campaigns: number;
        pipeline_value: number;
        lead_sources: Record<string, number>;
      }>('/api/v1/analytics/dashboard', token || undefined),
    enabled: !!token,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold">Analytics</h1>
      <p className="text-muted-foreground">Lead sources, pipeline value, and performance</p>

      <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Pipeline Value</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              TZS {Number(data?.pipeline_value ?? 0).toLocaleString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Conversion</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{data?.conversion_rate ?? 0}%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Avg Deal</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              TZS {Number(data?.avg_deal_value ?? 0).toLocaleString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Active Campaigns</CardTitle></CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{data?.active_campaigns ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader><CardTitle>Lead Sources</CardTitle></CardHeader>
        <CardContent>
          {data?.lead_sources && Object.keys(data.lead_sources).length > 0 ? (
            <ul className="space-y-2 text-sm">
              {Object.entries(data.lead_sources).map(([source, count]) => (
                <li key={source} className="flex justify-between">
                  <span className="capitalize">{source.replace('_', ' ')}</span>
                  <strong>{count}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No lead source data yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
