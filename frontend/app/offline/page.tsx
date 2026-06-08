'use client';

import { WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function OfflinePage() {
  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30 p-6 text-center">
      <div className="max-w-md rounded-2xl border border-kijani-200 bg-white p-8 shadow-lg">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-kijani-100 text-kijani-700 animate-bounce">
          <WifiOff className="h-8 w-8" />
        </div>

        <h1 className="mt-6 text-2xl font-bold text-kijani-950">Upo Nje ya Mtandao</h1>
        <p className="mt-2 text-sm text-kijani-700">
          Tafadhali angalia mtandao wako wa intaneti au Wi-Fi. Kijani AI itajirejesha kiotomatiki utakapounganishwa tena.
        </p>

        <div className="my-6 border-t border-kijani-100" />

        <h1 className="text-xl font-bold text-kijani-950">You Are Offline</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Please check your internet connection. Kijani AI will reconnect automatically once network service is restored.
        </p>

        <Button
          onClick={handleRetry}
          className="mt-8 w-full gap-2 bg-kijani-600 hover:bg-kijani-700 text-white"
        >
          <RefreshCw className="h-4 w-4" />
          Jaribu Tena / Retry
        </Button>
      </div>
    </div>
  );
}
