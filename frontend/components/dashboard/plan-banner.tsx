'use client';

import Link from 'next/link';
import { useUsage } from '@/hooks/useUsage';

export function PlanBanner() {
  const { data: usage } = useUsage();
  if (!usage) return null;

  const leadPct = (usage.leads_used / usage.leads_limit) * 100;
  const nearLimit = leadPct >= 80;
  const atLimit = usage.leads_remaining <= 0;

  if (!nearLimit && usage.onboarding_complete) return null;

  return (
    <div className="border-b bg-kijani-50 px-6 py-2 text-sm">
      {!usage.onboarding_complete && (
        <p>
          <Link href="/onboarding" className="font-medium text-kijani-700 underline">
            Complete setup / Kamilisha usanidi
          </Link>
          {' '}— connect WhatsApp and set your target market.
        </p>
      )}
      {atLimit && (
        <p className="text-red-700">
          Lead limit reached ({usage.leads_used}/{usage.leads_limit}).{' '}
          <Link href="/billing" className="underline font-medium">Upgrade plan / Boresha mpango</Link>
        </p>
      )}
      {nearLimit && !atLimit && (
        <p className="text-amber-800">
          {usage.leads_remaining} leads remaining on {usage.plan_type} plan.{' '}
          <Link href="/billing" className="underline">Upgrade</Link>
        </p>
      )}
    </div>
  );
}
