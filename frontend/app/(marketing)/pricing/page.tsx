'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Check, Minus, MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(false);

  return (
    <div className="min-h-screen bg-[#090D16] text-[#E2E8F0] font-sans selection:bg-[#10B981]/30 selection:text-white relative overflow-hidden flex flex-col justify-center py-16 px-4 sm:px-6 lg:px-8">
      {/* Background ambient glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-[#10B981]/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-blue-500/5 blur-[120px] pointer-events-none" />

      <div className="relative max-w-6xl mx-auto w-full space-y-12">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Pricing tiers — designed for Tanzania
          </h1>
          <p className="text-[#94A3B8] text-base max-w-xl mx-auto">
            All plans in Tanzanian Shillings. Pay via M-Pesa or bank transfer.
          </p>
        </div>

        {/* Toggle Switch */}
        <div className="flex items-center justify-center space-x-4">
          <span className={`text-sm font-medium transition-colors ${!isAnnual ? 'text-white' : 'text-[#64748B]'}`}>
            Monthly
          </span>
          <button
            onClick={() => setIsAnnual(!isAnnual)}
            className="w-12 h-6 rounded-full bg-[#1E293B] border border-[#334155] p-1 transition-colors duration-300 relative focus:outline-none focus:ring-2 focus:ring-[#10B981]/50"
            aria-label="Toggle pricing cycle"
          >
            <div
              className={`w-4 h-4 rounded-full bg-[#10B981] shadow-sm transform transition-transform duration-300 ${
                isAnnual ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
          <span className={`text-sm font-medium transition-colors flex items-center gap-1.5 ${isAnnual ? 'text-white' : 'text-[#64748B]'}`}>
            Annual
            <span className="text-xs bg-[#10B981]/10 text-[#10B981] px-2 py-0.5 rounded-full font-semibold">
              Save 20%
            </span>
          </span>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto items-stretch">
          
          {/* Bure - Free Tier */}
          <div className="relative rounded-2xl bg-[#0F172A]/80 border border-[#1E293B] p-8 flex flex-col justify-between backdrop-blur-md transition-all hover:border-[#334155] hover:translate-y-[-2px] shadow-xl">
            <div className="space-y-6">
              <div>
                <span className="text-[#94A3B8] text-xs font-semibold tracking-wider uppercase">Bure — Free</span>
                <div className="mt-4 flex items-baseline text-white">
                  <span className="text-4xl font-extrabold tracking-tight">TZS 0</span>
                  <span className="ml-1 text-sm font-medium text-[#64748B]">/mo</span>
                </div>
                <p className="mt-4 text-sm text-[#94A3B8]">
                  Get your first replies. No card needed, no tricks.
                </p>
              </div>

              <div className="h-px bg-[#1E293B]" />

              <ul className="space-y-4">
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">20 leads/month</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">1 active campaign</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">WhatsApp outreach</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">Swahili + English copy</span>
                </li>
                <li className="flex items-start text-[#64748B]">
                  <Minus className="h-5 w-5 shrink-0 mr-3" />
                  <span className="text-sm line-through decoration-[#334155]">No pipeline analytics</span>
                </li>
                <li className="flex items-start text-[#64748B]">
                  <Minus className="h-5 w-5 shrink-0 mr-3" />
                  <span className="text-sm line-through decoration-[#334155]">No team members</span>
                </li>
                <li className="flex items-start text-[#64748B]">
                  <Minus className="h-5 w-5 shrink-0 mr-3" />
                  <span className="text-sm line-through decoration-[#334155]">No BRELA enrichment</span>
                </li>
              </ul>
            </div>

            <div className="mt-8">
              <Link href="/register?plan=free">
                <Button className="w-full bg-[#1E293B] hover:bg-[#334155] text-white border border-[#334155]" variant="outline">
                  Start free
                </Button>
              </Link>
            </div>
          </div>

          {/* Biashara - Growth Tier */}
          <div className="relative rounded-2xl bg-[#0F172A]/90 border-2 border-[#10B981] p-8 flex flex-col justify-between backdrop-blur-md shadow-[0_0_25px_rgba(16,185,129,0.15)] transition-all hover:translate-y-[-2px]">
            {/* Most popular badge */}
            <div className="absolute top-0 right-8 transform -translate-y-1/2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#10B981] text-[#090D16]">
                Most popular
              </span>
            </div>

            <div className="space-y-6">
              <div>
                <span className="text-[#10B981] text-xs font-bold tracking-wider uppercase">Biashara — Growth</span>
                <div className="mt-4 flex flex-col">
                  <div className="flex items-baseline text-white">
                    <span className="text-4xl font-extrabold tracking-tight">
                      TZS {isAnnual ? '60,000' : '75,000'}
                    </span>
                    <span className="ml-1 text-sm font-medium text-[#64748B]">/mo</span>
                  </div>
                  {isAnnual && (
                    <span className="text-xs text-[#10B981] mt-1 font-medium">
                      Billed TZS 720,000 annually
                    </span>
                  )}
                </div>
                <p className="mt-4 text-sm text-[#94A3B8]">
                  For SMEs ready to run real campaigns and grow a pipeline.
                </p>
              </div>

              <div className="h-px bg-[#1E293B]" />

              <ul className="space-y-4">
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-white font-medium">200 leads/month</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">5 active campaigns</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">WhatsApp + voice notes</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">BRELA enrichment</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">Pipeline Kanban + analytics</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">3 team members</span>
                </li>
                <li className="flex items-start text-[#64748B]">
                  <Minus className="h-5 w-5 shrink-0 mr-3" />
                  <span className="text-sm line-through decoration-[#334155]">No white-label</span>
                </li>
              </ul>
            </div>

            <div className="mt-8">
              <Link href={`/register?plan=growth&billing=${isAnnual ? 'annual' : 'monthly'}`}>
                <Button className="w-full bg-[#10B981] hover:bg-[#059669] text-[#090D16] font-bold">
                  Start 14-day trial
                </Button>
              </Link>
            </div>
          </div>

          {/* Shirika - Agency Tier */}
          <div className="relative rounded-2xl bg-[#0F172A]/80 border border-[#1E293B] p-8 flex flex-col justify-between backdrop-blur-md transition-all hover:border-[#334155] hover:translate-y-[-2px] shadow-xl">
            <div className="space-y-6">
              <div>
                <span className="text-[#94A3B8] text-xs font-semibold tracking-wider uppercase">Shirika — Agency</span>
                <div className="mt-4 flex flex-col">
                  <div className="flex items-baseline text-white">
                    <span className="text-4xl font-extrabold tracking-tight">
                      TZS {isAnnual ? '160,000' : '200,000'}
                    </span>
                    <span className="ml-1 text-sm font-medium text-[#64748B]">/mo</span>
                  </div>
                  {isAnnual && (
                    <span className="text-xs text-[#10B981] mt-1 font-medium">
                      Billed TZS 1,920,000 annually
                    </span>
                  )}
                </div>
                <p className="mt-4 text-sm text-[#94A3B8]">
                  For agencies running campaigns on behalf of multiple clients.
                </p>
              </div>

              <div className="h-px bg-[#1E293B]" />

              <ul className="space-y-4">
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">1,000 leads/month</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">Unlimited campaigns</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">Multi-tenant client accounts</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">White-label dashboard</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">Priority support (WhatsApp)</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">Unlimited team members</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-[#10B981] shrink-0 mr-3" />
                  <span className="text-sm text-[#E2E8F0]">Custom Swahili AI persona</span>
                </li>
              </ul>
            </div>

            <div className="mt-8">
              <Link href="https://wa.me/255799999999?text=Habari!%20I%20want%20to%20learn%20more%20about%20Shirika%20Agency%20Plan%20for%20Kijani%20AI" target="_blank">
                <Button className="w-full bg-[#1E293B] hover:bg-[#334155] text-white border border-[#334155]" variant="outline">
                  Contact us
                </Button>
              </Link>
            </div>
          </div>

        </div>

        {/* Payment & Support Info Note */}
        <div className="max-w-5xl mx-auto rounded-xl bg-[#0F172A]/40 border border-[#1E293B] p-4 flex flex-col sm:flex-row items-center space-y-3 sm:space-y-0 sm:space-x-4 text-center sm:text-left justify-center backdrop-blur-sm">
          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-[#10B981]/10 text-[#10B981]">
            <MessageCircle className="h-5 w-5" />
          </div>
          <p className="text-xs sm:text-sm text-[#94A3B8]">
            <span className="font-bold text-white">Lipa kwa M-Pesa</span> — Pay via M-Pesa Lipa Na, CRDB, or NMB transfer. No international card required. Questions? WhatsApp us at <span className="font-semibold text-white">+255 799 999 999</span>.
          </p>
        </div>

      </div>
    </div>
  );
}
