'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useApproveOutreach, usePendingOutreach } from '@/hooks/useInteractions';

export default function OutreachApprovalPage() {
  const { data: pending = [], isLoading } = usePendingOutreach();
  const approve = useApproveOutreach();

  return (
    <div>
      <h1 className="text-2xl font-bold">Outreach Approval</h1>
      <p className="text-muted-foreground">
        Review and approve AI-generated messages before sending via WhatsApp
      </p>

      {isLoading ? (
        <p className="mt-6">Loading...</p>
      ) : pending.length === 0 ? (
        <Card className="mt-6">
          <CardContent className="py-12 text-center text-muted-foreground">
            No messages pending approval.
          </CardContent>
        </Card>
      ) : (
        <div className="mt-6 space-y-4">
          {pending.map((item) => (
            <Card key={item.id}>
              <CardHeader>
                <CardTitle className="text-base capitalize">{item.channel} · {item.direction}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm whitespace-pre-wrap">{item.content}</p>
                <Button
                  onClick={() => approve.mutate(item.id)}
                  disabled={approve.isPending}
                >
                  Approve & Send
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
