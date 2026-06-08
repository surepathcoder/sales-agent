import { Menu } from 'lucide-react';
import { useAuthStore } from '@/lib/auth';
import { Button } from '@/components/ui/button';

interface TopbarProps {
  onMenuClick?: () => void;
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { user, tenant, logout } = useAuthStore();

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-4 md:px-6">
      <div className="flex items-center gap-3">
        {onMenuClick && (
          <button
            onClick={onMenuClick}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted md:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <div>
          <p className="text-xs text-muted-foreground md:text-sm">Tenant</p>
          <p className="text-sm font-medium md:text-base">{tenant?.name || '—'}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 md:gap-4">
        <span className="hidden rounded-full bg-kijani-100 px-3 py-1 text-xs font-medium text-kijani-700 sm:inline-block">
          {tenant?.plan_type?.toUpperCase()}
        </span>
        <span className="text-xs md:text-sm text-muted-foreground max-w-[120px] truncate md:max-w-none">
          {user?.email}
        </span>
        <Button variant="outline" size="sm" className="h-8 text-xs md:h-9 md:text-sm" onClick={logout}>
          Logout
        </Button>
      </div>
    </header>
  );
}
