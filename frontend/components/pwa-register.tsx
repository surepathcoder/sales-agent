'use client';

import { useEffect } from 'react';
import { useToast } from '@/components/ui/toast';

export function PwaRegister() {
  const { toast } = useToast();

  useEffect(() => {
    // 1) Register Service Worker
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker
          .register('/sw.js')
          .then((registration) => {
            console.log('Kijani SW registered with scope: ', registration.scope);
          })
          .catch((err) => {
            console.error('Kijani SW registration failed: ', err);
          });
      });
    }

    // 2) Listen to Online/Offline Connection Events
    const handleOnline = () => {
      toast('✓ Umerudi mtandaoni / Back online', 'success');
    };

    const handleOffline = () => {
      toast('✗ Upo nje ya mtandao / You are offline', 'error');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial check (if loaded while offline)
    if (typeof window !== 'undefined' && !navigator.onLine) {
      handleOffline();
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [toast]);

  return null;
}
