'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

export default function DashboardHomePage() {
  const token = useAuthStore((s) => s.accessToken);
  const { data } = useQuery({
    queryKey: ['analytics'],
    queryFn: () =>
      api.get<{
        total_leads: number;
        conversion_rate: number;
        avg_deal_value: number;
        active_campaigns: number;
        pipeline_value: number;
      }>('/api/v1/analytics/dashboard', token || undefined),
    enabled: !!token,
  });

  const stats = [
    { label: 'Total Leads', value: data?.total_leads ?? '—' },
    { label: 'Conversion Rate', value: data ? `${data.conversion_rate}%` : '—' },
    { label: 'Avg Deal Value', value: data ? `TZS ${Number(data.avg_deal_value).toLocaleString()}` : '—' },
    { label: 'Active Campaigns', value: data?.active_campaigns ?? '—' },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p className="text-muted-foreground">Karibu — Welcome to Kijani AI</p>

      <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
