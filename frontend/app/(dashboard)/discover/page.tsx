"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Send, Loader2, Search, CheckCircle2, MapPin, Globe, Phone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApprovalQueue } from "@/components/discovery/ApprovalQueue";
import { useAuthStore } from "@/lib/auth";
import { api } from "@/lib/api";

export default function DiscoverPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [submittedPrompt, setSubmittedPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const feedEndRef = useRef<HTMLDivElement>(null);

  const token = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [status]);

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const data = await api.get<any>(`/api/v1/agents/job/${jobId}`, token || undefined);
        setStatus(data);

        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
          setIsLoading(false);
          if (data.status === "completed" && data.lead_ids?.length > 0) {
            fetchLeads(data.lead_ids);
          } else if (data.status === "failed") {
            setError(data.error || "Discovery failed.");
          } else if (data.status === "completed" && !data.lead_ids?.length) {
            setError("No leads found. Try a different query or location.");
          }
        }
      } catch (err) {
        console.error("Failed to poll job:", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId, token]);

  const fetchLeads = async (leadIds: string[]) => {
    try {
      const results: any[] = [];
      for (const id of leadIds) {
        try {
          const lead = await api.get<any>(`/api/v1/leads/${id}`, token || undefined);
          results.push({
            id: lead.id,
            company_name: lead.company_name,
            phone: lead.custom_fields?.phone,
            website: lead.custom_fields?.website,
            address: lead.address,
            score: lead.lead_score || lead.ai_insights?.initial_score?.score || 50,
            reasoning: lead.ai_insights?.initial_score?.reasoning || "Discovered by AI Scout",
          });
        } catch { /* skip */ }
      }
      setLeads(results);
    } catch (err) {
      console.error("Failed to fetch leads:", err);
    }
  };

  const handleApprove = async (selectedIds: string[]) => {
    try {
      const campaign = await api.post<any>("/api/v1/campaigns", {
        name: `Discovery — ${submittedPrompt.slice(0, 40)}`,
        campaign_type: "outbound_sequence",
        agent_configuration: { human_approval_required: true },
        sequence_steps: [{ step_order: 1, channel: "whatsapp", delay_hours: 0 }],
        lead_pool: selectedIds,
      }, token || undefined);
      await api.post(`/api/v1/campaigns/${campaign.id}/start`, {}, token || undefined);
      router.push(`/campaigns`);
    } catch (err) {
      console.error("Approval failed:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    setSubmittedPrompt(prompt);
    setIsLoading(true);
    setError(null);
    setJobId(null);
    setStatus(null);
    setLeads([]);
    try {
      const data = await api.post<any>("/api/v1/agents/discover/chat", { prompt }, token || undefined);
      setJobId(data.job_id);
    } catch (err: any) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const events: any[] = status?.events || [];
  const savedCount: number = status?.saved_count || 0;
  const total: number = status?.total || 0;
  const progressPct: number = status?.progress_pct || 0;
  const isDone = status?.status === "completed";
  const isFailed = status?.status === "failed";

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-5xl mx-auto px-4 py-6">
      <div className="mb-5">
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          AI Discovery Agent
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Tell the AI what businesses to find. It scouts Google Maps in real-time, enriches each lead, then hands them to you for approval.
        </p>
      </div>

      <div className="flex-1 bg-card border border-border rounded-2xl shadow-sm flex flex-col overflow-hidden">

        {/* Live Feed */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">

          {/* Greeting */}
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
            </div>
            <div className="bg-muted px-4 py-3 rounded-2xl rounded-tl-none max-w-[80%] text-sm">
              <p>Hello! I'm your AI Sales Scout.</p>
              <p className="text-xs text-muted-foreground mt-1">Try: <em>"Find me 50 hardware stores in Arusha"</em></p>
            </div>
          </div>

          {/* User message */}
          {submittedPrompt && (
            <div className="flex gap-3 justify-end">
              <div className="bg-primary px-4 py-3 rounded-2xl rounded-tr-none max-w-[80%] text-primary-foreground text-sm">
                {submittedPrompt}
              </div>
            </div>
          )}

          {/* Status panel */}
          {status && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center shrink-0 mt-0.5">
                <Search className="h-3.5 w-3.5 text-primary" />
              </div>
              <div className="bg-muted px-4 py-3 rounded-2xl rounded-tl-none border border-border/60 max-w-[90%] w-full space-y-2">
                {/* Header */}
                <div className="flex items-center gap-2">
                  {!isDone && !isFailed && <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />}
                  {isDone && <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />}
                  <span className="font-semibold text-sm">
                    {isDone
                      ? `Discovery Complete — ${savedCount} lead${savedCount !== 1 ? "s" : ""} found ✓`
                      : isFailed
                      ? "Discovery Failed"
                      : total > 0
                      ? `Scouting… ${savedCount}/${total} saved`
                      : "Scouting…"}
                  </span>
                </div>

                {/* Progress bar */}
                {progressPct > 0 && (
                  <div className="w-full bg-background rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-primary h-full transition-all duration-500"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                )}

                {/* Limit warning */}
                {status.limit_warning && (
                  <div className="p-2 bg-yellow-500/10 border border-yellow-500/20 rounded-md text-xs text-yellow-600 dark:text-yellow-400">
                    ⚠️ {status.limit_warning}
                  </div>
                )}

                {/* Live event log */}
                {events.length > 0 && (
                  <div className="mt-1 space-y-0.5 max-h-40 overflow-y-auto">
                    {events.map((ev: any, i: number) => (
                      <div key={i} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                        <span className="text-primary/60 shrink-0">›</span>
                        <span>{ev.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
                <span className="text-red-500 font-bold text-xs">!</span>
              </div>
              <div className="bg-red-500/10 border border-red-500/20 px-4 py-3 rounded-2xl rounded-tl-none max-w-[80%] text-red-600 dark:text-red-400 text-sm">
                {error}
              </div>
            </div>
          )}

          <div ref={feedEndRef} />
        </div>

        {/* HITL Approval Table */}
        {leads.length > 0 && (
          <div className="border-t border-border bg-background">
            <ApprovalQueue leads={leads} onApprove={handleApprove} />
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-border bg-background">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isLoading}
              placeholder='e.g. "Find me 50 hardware stores in Arusha"'
              className="flex-1 bg-muted border border-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50"
            />
            <Button
              type="submit"
              disabled={isLoading || !prompt.trim()}
              className="rounded-xl px-6"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
