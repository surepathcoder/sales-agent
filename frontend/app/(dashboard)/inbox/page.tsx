'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useApproveOutreach } from '@/hooks/useInteractions';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';

interface InboxItem {
  id: string;
  lead_id: string;
  channel: string;
  direction: string;
  content: string;
  ai_generated: boolean;
  human_approved: boolean | null;
  created_at: string;
}

export default function InboxPage() {
  const token = useAuthStore((s) => s.accessToken);
  const approve = useApproveOutreach();

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['inbox'],
    queryFn: () => api.get<InboxItem[]>('/api/v1/interactions', token || undefined),
    enabled: !!token,
    refetchInterval: 10000,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold">Inbox / Kikasha</h1>
      <p className="text-muted-foreground">WhatsApp messages — approve AI drafts before sending</p>

      {isLoading ? (
        <p className="mt-6">Loading...</p>
      ) : items.length === 0 ? (
        <Card className="mt-6">
          <CardContent className="py-12 text-center text-muted-foreground">
            No messages yet. Run outreach on a lead or start a campaign.
          </CardContent>
        </Card>
      ) : (
        <div className="mt-6 space-y-3">
          {items.map((item) => (
            <Card key={item.id}>
              <CardContent className="flex items-start justify-between gap-4 pt-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span className="capitalize">{item.direction}</span>
                    <span>·</span>
                    <span className="capitalize">{item.channel}</span>
                    <span>·</span>
                    <span>{new Date(item.created_at).toLocaleString()}</span>
                    <Link href={`/leads/${item.lead_id}`} className="text-kijani-600 underline">
                      View lead
                    </Link>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-sm">{item.content}</p>
                </div>
                {item.human_approved === null && item.ai_generated && item.direction === 'outbound' && (
                  <Button size="sm" onClick={() => approve.mutate(item.id)} disabled={approve.isPending}>
                    Approve & Send
                  </Button>
                )}
                {item.human_approved && (
                  <span className="text-xs text-green-700">Sent ✓</span>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
