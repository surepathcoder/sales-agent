'use client';

export function AgentStatus({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: 'bg-amber-400',
    completed: 'bg-green-400',
    failed: 'bg-red-400',
    queued: 'bg-blue-400',
  };

  return (
    <span className="inline-flex items-center gap-2 text-sm">
      <span className={`h-2 w-2 rounded-full ${colors[status] || 'bg-gray-400'}`} />
      {status}
    </span>
  );
}
