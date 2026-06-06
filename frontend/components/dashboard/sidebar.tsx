'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  CreditCard,
  LayoutDashboard,
  Megaphone,
  Inbox,
  MessageSquare,
  Settings,
  Users,
  Target,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const nav = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/leads', label: 'Leads / Wateja', icon: Users },
  { href: '/inbox', label: 'Inbox / Kikasha', icon: Inbox },
  { href: '/campaigns', label: 'Campaigns', icon: Megaphone },
  { href: '/outreach', label: 'Outreach', icon: MessageSquare },
  { href: '/deals', label: 'Deals', icon: Target },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/billing', label: 'Billing', icon: CreditCard },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-kijani-900 text-white">
      <div className="flex h-16 items-center px-6">
        <span className="text-xl font-bold">🌿 Kijani AI</span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {nav.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
              pathname === href || (href !== '/' && pathname.startsWith(href))
                ? 'bg-kijani-700 text-white'
                : 'text-kijani-100 hover:bg-kijani-800'
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>
      <div className="border-t border-kijani-800 p-4">
        <div className="flex items-center gap-2 text-xs text-kijani-200">
          <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
          Agents active
        </div>
      </div>
    </aside>
  );
}
