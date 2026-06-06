'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCampaigns } from '@/hooks/useCampaigns';

export default function CampaignsPage() {
  const { data: campaigns = [], isLoading } = useCampaigns();

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Campaigns</h1>
        <Link href="/campaigns/new">
          <Button>New Campaign</Button>
        </Link>
      </div>

      {isLoading ? (
        <p className="mt-6">Loading...</p>
      ) : campaigns.length === 0 ? (
        <Card className="mt-6">
          <CardContent className="py-12 text-center text-muted-foreground">
            No campaigns yet. Create your first outbound sequence.
          </CardContent>
        </Card>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {campaigns.map((c) => (
            <Link key={c.id} href={`/campaigns/${c.id}`}>
              <Card className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="text-lg">{c.name}</CardTitle>
                  <span className="text-xs capitalize text-muted-foreground">{c.status}</span>
                </CardHeader>
                <CardContent className="text-sm">
                  <p>{c.contacted_count}/{c.total_leads} contacted</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
