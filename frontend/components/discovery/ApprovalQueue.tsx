"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface Lead {
  id: string;
  company_name: string;
  phone?: string;
  website?: string;
  score?: number;
  reasoning?: any;
}

interface ApprovalQueueProps {
  leads: Lead[];
  onApprove: (selectedIds: string[]) => void;
}

function formatReasoning(reasoning: any): string {
  if (!reasoning) return "";
  if (typeof reasoning === "string") return reasoning;
  if (Array.isArray(reasoning)) return reasoning.join("; ");
  if (typeof reasoning === "object") {
    return Object.entries(reasoning)
      .map(([key, val]) => `${key.replace(/_/g, " ")}: ${val}`)
      .join("; ");
  }
  return String(reasoning);
}

export function ApprovalQueue({ leads, onApprove }: ApprovalQueueProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set(leads.map(l => l.id)));

  const toggleLead = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  const handleApprove = () => {
    onApprove(Array.from(selectedIds));
  };

  if (leads.length === 0) return null;

  return (
    <div className="mt-8 bg-card border border-border rounded-xl shadow-lg overflow-hidden">
      <div className="p-4 border-b border-border flex justify-between items-center bg-muted/30">
        <div>
          <h3 className="font-semibold text-foreground">Discovered Leads</h3>
          <p className="text-sm text-muted-foreground">Select leads to approve for outreach</p>
        </div>
        <Button 
          onClick={handleApprove}
          disabled={selectedIds.size === 0}
          className="bg-primary text-primary-foreground"
        >
          Approve {selectedIds.size} Leads & Create Campaign
        </Button>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-muted-foreground uppercase bg-muted/50">
            <tr>
              <th className="px-4 py-3 w-10">
                <input 
                  type="checkbox" 
                  checked={selectedIds.size === leads.length && leads.length > 0}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedIds(new Set(leads.map(l => l.id)));
                    } else {
                      setSelectedIds(new Set());
                    }
                  }}
                  className="rounded border-border bg-background"
                />
              </th>
              <th className="px-4 py-3">Company</th>
              <th className="px-4 py-3">Contact</th>
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">AI Reasoning</th>
            </tr>
          </thead>
          <tbody>
            {leads.map(lead => (
              <tr key={lead.id} className="border-b border-border hover:bg-muted/20">
                <td className="px-4 py-3">
                  <input 
                    type="checkbox" 
                    checked={selectedIds.has(lead.id)}
                    onChange={() => toggleLead(lead.id)}
                    className="rounded border-border bg-background"
                  />
                </td>
                <td className="px-4 py-3 font-medium">{lead.company_name}</td>
                <td className="px-4 py-3">
                  <div className="text-xs">{lead.phone || 'No phone'}</div>
                  <div className="text-xs text-muted-foreground">{lead.website}</div>
                </td>
                <td className="px-4 py-3">
                  {lead.score ? (
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${lead.score >= 70 ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'}`}>
                      {lead.score}/100
                    </span>
                  ) : '-'}
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground max-w-xs truncate" title={formatReasoning(lead.reasoning)}>
                  {formatReasoning(lead.reasoning) || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

