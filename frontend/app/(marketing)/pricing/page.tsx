import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { PLAN_FEATURES } from '@/lib/constants';
import type { PlanType } from '@/types';

export default function PricingPage() {
  return (
    <div className="min-h-screen px-8 py-16">
      <h1 className="text-center text-3xl font-bold">Pricing (TZS)</h1>
      <div className="mx-auto mt-12 grid max-w-4xl gap-6 md:grid-cols-2 lg:grid-cols-4">
        {(Object.keys(PLAN_FEATURES) as PlanType[]).map((plan) => (
          <div key={plan} className="rounded-lg border p-6">
            <h2 className="text-lg font-semibold capitalize">{plan}</h2>
            <p className="mt-2 text-2xl font-bold">
              {PLAN_FEATURES[plan].price === 0 ? 'Free' : `TZS ${PLAN_FEATURES[plan].price.toLocaleString()}/mo`}
            </p>
            <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
              <li>{PLAN_FEATURES[plan].leads} leads</li>
              <li>{PLAN_FEATURES[plan].campaigns} campaigns</li>
            </ul>
            <Link href="/register" className="mt-6 block">
              <Button className="w-full" variant={plan === 'growth' ? 'default' : 'outline'}>
                Get Started
              </Button>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
