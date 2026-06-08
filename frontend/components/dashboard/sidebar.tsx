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
  X,
  Shield,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/auth';

const nav = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/discover', label: 'AI Discover', icon: Sparkles },
  { href: '/leads', label: 'Leads / Wateja', icon: Users },
  { href: '/inbox', label: 'Inbox / Kikasha', icon: Inbox },
  { href: '/campaigns', label: 'Campaigns', icon: Megaphone },
  { href: '/outreach', label: 'Outreach', icon: MessageSquare },
  { href: '/deals', label: 'Deals', icon: Target },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/billing', label: 'Billing', icon: CreditCard },
  { href: '/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);

  return (
    <>
      {/* Backdrop overlay for mobile drawer */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 transition-opacity md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex h-screen w-64 flex-col border-r bg-kijani-900 text-white transition-transform duration-300 md:relative md:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between px-6">
          <span className="text-xl font-bold">🌿 Kijani AI</span>
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-kijani-200 hover:bg-kijani-800 hover:text-white md:hidden"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={onClose}
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
          {user?.role === 'super_admin' && (
            <Link
              href="/admin"
              onClick={onClose}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition-colors mt-4 border border-amber-500/30',
                pathname === '/admin' || pathname.startsWith('/admin')
                  ? 'bg-amber-600 text-white border-amber-500'
                  : 'text-amber-300 hover:bg-amber-950/40 hover:text-amber-200'
              )}
            >
              <Shield className="h-4 w-4 text-amber-400" />
              Super Admin Panel
            </Link>
          )}
        </nav>
        <div className="border-t border-kijani-800 p-4">
          <div className="flex items-center gap-2 text-xs text-kijani-200">
            <span className="h-2 w-2 rounded-full bg-green-400 animate-pulse" />
            Agents active
          </div>
        </div>
      </aside>
    </>
  );
}
