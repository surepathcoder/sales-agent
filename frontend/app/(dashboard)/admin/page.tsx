'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/auth';
import { api } from '@/lib/api';
import { useToast } from '@/components/ui/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Building2,
  Megaphone,
  ShieldAlert,
  CreditCard,
  Activity,
  CheckCircle2,
  PauseCircle,
  RefreshCw,
  AlertTriangle,
  Shield,
  ShieldCheck,
  Ban,
  ArrowRight,
} from 'lucide-react';

// --- TYPES ---
interface Organization {
  id: string;
  name: string;
  slug: string;
  plan_type: string;
  status: string;
  users_count: number;
  leads_count: number;
  campaigns_count: number;
  settings: Record<string, any>;
}

interface Campaign {
  id: string;
  name: string;
  organization_name: string;
  campaign_type: string;
  status: string;
  total_leads: number;
  contacted_count: number;
  engaged_count: number;
}

interface AbuseReport {
  id: string;
  tenant_name: string;
  reporter_number: string;
  report_type: string;
  details: string;
  status: string;
  notes: string;
  created_at: string;
}

interface Payment {
  id: string;
  tenant_name: string;
  transaction_type: string;
  amount: number;
  currency: string;
  payment_method: string;
  payment_reference: string;
  status: string;
  created_at: string;
  completed_at?: string;
}

interface Telemetry {
  telephony: {
    active_outbound_channels: number;
    max_channels_cap: number;
    rate_limit_calls_per_min: number;
    successful_transfers_today: number;
  };
  crm_sync: {
    salesforce_sync_status: string;
    hubspot_sync_status: string;
    last_sync_timestamp: string;
    sync_records_processed_24h: number;
  };
  globals: {
    total_leads_processed: number;
    total_campaigns_created: number;
    total_abuse_reports_logged: number;
    total_payment_txns_processed: number;
  };
}

export default function AdminDashboard() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.accessToken);
  const { toast } = useToast();

  // Route Guard
  useEffect(() => {
    if (user && user.role !== 'super_admin') {
      toast('Forbidden: Super Admins Only / Walinzi Wakuu Pekee', 'error');
      router.replace('/dashboard');
    }
  }, [user, router, toast]);

  const [activeTab, setActiveTab] = useState<'organizations' | 'campaigns' | 'abuse' | 'payments' | 'telemetry'>('organizations');
  const [loading, setLoading] = useState(true);

  // States
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [reports, setReports] = useState<AbuseReport[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);

  // Edit Org States
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [orgPlan, setOrgPlan] = useState<string>('');
  const [orgStatus, setOrgStatus] = useState<string>('');
  const [orgMaxLeads, setOrgMaxLeads] = useState<number>(1000);
  const [orgMaxCampaigns, setOrgMaxCampaigns] = useState<number>(10);

  // Resolve Abuse State
  const [resolvingReport, setResolvingReport] = useState<AbuseReport | null>(null);
  const [resolveStatus, setResolveStatus] = useState<string>('resolved');
  const [resolveNotes, setResolveNotes] = useState<string>('');
  const [suspendTenant, setSuspendTenant] = useState<boolean>(false);

  // Fetch Data
  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'organizations') {
        const data = await api.get<Organization[]>('/api/v1/admin/organizations', token || undefined);
        setOrgs(data);
      } else if (activeTab === 'campaigns') {
        const data = await api.get<Campaign[]>('/api/v1/admin/campaigns', token || undefined);
        setCampaigns(data);
      } else if (activeTab === 'abuse') {
        const data = await api.get<AbuseReport[]>('/api/v1/admin/abuse-reports', token || undefined);
        setReports(data);
      } else if (activeTab === 'payments') {
        const data = await api.get<Payment[]>('/api/v1/admin/payments', token || undefined);
        setPayments(data);
      } else if (activeTab === 'telemetry') {
        const data = await api.get<Telemetry>('/api/v1/admin/telemetry', token || undefined);
        setTelemetry(data);
      }
    } catch (err: any) {
      toast(err.message || 'Failed to fetch data / Kushindwa kupakia data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && user.role === 'super_admin') {
      fetchData();
    }
  }, [activeTab, user]);

  // Operations: Org
  const handleUpdateOrg = async () => {
    if (!editingOrg) return;
    try {
      await api.patch(`/api/v1/admin/organizations/${editingOrg.id}`, {
        plan_type: orgPlan,
        status: orgStatus,
        max_leads: orgMaxLeads,
        max_campaigns: orgMaxCampaigns,
      }, token || undefined);
      toast('Organization updated / Shirika limeboreshwa', 'success');
      setEditingOrg(null);
      fetchData();
    } catch (err: any) {
      toast(err.message || 'Update failed / Kushindwa kuboresha', 'error');
    }
  };

  // Operations: Campaigns
  const handlePauseCampaign = async (campaignId: string) => {
    try {
      await api.post(`/api/v1/admin/campaigns/${campaignId}/pause`, {}, token || undefined);
      toast('Campaign paused (Emergency) / Kampeni imesimamishwa kwa dharura', 'success');
      fetchData();
    } catch (err: any) {
      toast(err.message || 'Failed to pause / Imeshindwa kusimamisha', 'error');
    }
  };

  const handleApproveCampaign = async (campaignId: string) => {
    try {
      await api.post(`/api/v1/admin/campaigns/${campaignId}/approve`, {}, token || undefined);
      toast('Campaign approved for compliance / Kampeni imeidhinishwa', 'success');
      fetchData();
    } catch (err: any) {
      toast(err.message || 'Failed to approve / Imeshindwa kuidhinisha', 'error');
    }
  };

  // Operations: Abuse Resolve
  const handleResolveAbuse = async () => {
    if (!resolvingReport) return;
    try {
      await api.post(`/api/v1/admin/abuse-reports/${resolvingReport.id}/resolve`, {
        status: resolveStatus,
        notes: resolveNotes,
        suspend_tenant: suspendTenant,
      }, token || undefined);
      toast('Abuse report resolved / Ripoti ya malalamiko imeshughulikiwa', 'success');
      setResolvingReport(null);
      fetchData();
    } catch (err: any) {
      toast(err.message || 'Failed to resolve / Imeshindwa kushughulikia', 'error');
    }
  };

  // Operations: Refund
  const handleRefund = async (paymentId: string) => {
    if (!confirm('Are you sure you want to process this refund? / Una uhakika unataka kurejesha malipo haya?')) return;
    try {
      await api.post(`/api/v1/admin/payments/${paymentId}/refund`, {}, token || undefined);
      toast('Refund processed and balance rolled back / Rejesho limekamilika na salio limeondolewa', 'success');
      fetchData();
    } catch (err: any) {
      toast(err.message || 'Refund failed / Rejesho limeshindikana', 'error');
    }
  };

  if (!user || user.role !== 'super_admin') {
    return null; // Route guarded
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-amber-500/20 pb-4">
        <div>
          <h1 className="text-3xl font-extrabold text-amber-500 flex items-center gap-2">
            <Shield className="h-8 w-8 text-amber-400" />
            Super Admin Panel / Jopo la Msimamizi Mkuu
          </h1>
          <p className="text-muted-foreground mt-1">
            Global system overrides, billing compliance, spam filters, and multi-tenant quotas.
          </p>
        </div>
        <div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 border-amber-500/30 text-amber-600 hover:bg-amber-500/10 hover:text-amber-500"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Data / Pakia Upya
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b pb-px overflow-x-auto">
        {[
          { id: 'organizations', label: 'Organizations / Mashirika', icon: Building2 },
          { id: 'campaigns', label: 'Campaigns / Kampeni', icon: Megaphone },
          { id: 'abuse', label: 'Abuse / Malalamiko', icon: ShieldAlert },
          { id: 'payments', label: 'Payments / Malipo', icon: CreditCard },
          { id: 'telemetry', label: 'Telemetry / Mifumo', icon: Activity },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? 'border-amber-500 text-amber-500 bg-amber-500/5'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="h-8 w-8 animate-spin text-amber-500" />
            <span className="text-sm text-muted-foreground">Loading data... / Inapakia data...</span>
          </div>
        </div>
      ) : (
        <div className="space-y-6 animate-fadeIn">
          {/* TAB 1: ORGANIZATIONS */}
          {activeTab === 'organizations' && (
            <Card className="border-amber-500/10">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-xl">Tenant Organizations / Mashirika ya Wateja</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b bg-muted/30">
                      <th className="p-3">Name / Jina</th>
                      <th className="p-3">Plan / Kifurushi</th>
                      <th className="p-3">Status / Hali</th>
                      <th className="p-3 text-right">Users</th>
                      <th className="p-3 text-right">Leads</th>
                      <th className="p-3 text-right">Campaigns</th>
                      <th className="p-3 text-center">Actions / Hatua</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orgs.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-muted-foreground">
                          No organizations found. / Hakuna mashirika yaliyopatikana.
                        </td>
                      </tr>
                    ) : (
                      orgs.map((org) => (
                        <tr key={org.id} className="border-b hover:bg-muted/10 transition-colors">
                          <td className="p-3 font-semibold">
                            {org.name}
                            <span className="block text-xs font-normal text-muted-foreground">/{org.slug}</span>
                          </td>
                          <td className="p-3">
                            <span className="px-2 py-0.5 rounded-full text-xs font-semibold uppercase bg-kijani-100 text-kijani-800">
                              {org.plan_type}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${
                              org.status === 'active'
                                ? 'bg-green-100 text-green-800'
                                : org.status === 'suspended'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {org.status === 'active' ? 'Active / Kazi' : org.status === 'suspended' ? 'Suspended / Imefungwa' : org.status}
                            </span>
                          </td>
                          <td className="p-3 text-right">{org.users_count}</td>
                          <td className="p-3 text-right">{org.leads_count}</td>
                          <td className="p-3 text-right">{org.campaigns_count}</td>
                          <td className="p-3 text-center">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setEditingOrg(org);
                                setOrgPlan(org.plan_type);
                                setOrgStatus(org.status);
                                setOrgMaxLeads(org.settings?.max_leads ?? 1000);
                                setOrgMaxCampaigns(org.settings?.max_campaigns ?? 10);
                              }}
                              className="text-amber-600 border-amber-500/30 hover:bg-amber-500/10"
                            >
                              Edit limits / Badili
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}

          {/* TAB 2: CAMPAIGNS */}
          {activeTab === 'campaigns' && (
            <Card className="border-amber-500/10">
              <CardHeader>
                <CardTitle className="text-xl">Outbound Sales Campaigns / Kampeni za Mauzo</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b bg-muted/30">
                      <th className="p-3">Campaign / Kampeni</th>
                      <th className="p-3">Organization / Shirika</th>
                      <th className="p-3">Type / Aina</th>
                      <th className="p-3">Status / Hali</th>
                      <th className="p-3 text-right">Leads</th>
                      <th className="p-3 text-right">Contacted</th>
                      <th className="p-3 text-right">Engaged</th>
                      <th className="p-3 text-center">Controls / Hatua</th>
                    </tr>
                  </thead>
                  <tbody>
                    {campaigns.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="p-8 text-center text-muted-foreground">
                          No campaigns active. / Hakuna kampeni zinazofanya kazi.
                        </td>
                      </tr>
                    ) : (
                      campaigns.map((c) => (
                        <tr key={c.id} className="border-b hover:bg-muted/10 transition-colors">
                          <td className="p-3 font-semibold">{c.name}</td>
                          <td className="p-3 text-muted-foreground">{c.organization_name}</td>
                          <td className="p-3 capitalize">{c.campaign_type.replace('_', ' ')}</td>
                          <td className="p-3">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${
                              c.status === 'running'
                                ? 'bg-green-100 text-green-800'
                                : c.status === 'paused'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {c.status}
                            </span>
                          </td>
                          <td className="p-3 text-right font-medium">{c.total_leads}</td>
                          <td className="p-3 text-right">{c.contacted_count}</td>
                          <td className="p-3 text-right text-green-600 font-semibold">{c.engaged_count}</td>
                          <td className="p-3 text-center space-x-2">
                            {c.status === 'running' && (
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handlePauseCampaign(c.id)}
                                className="bg-red-600 text-white hover:bg-red-700 flex items-center gap-1 mx-auto"
                              >
                                <PauseCircle className="h-4 w-4" />
                                Pause / Simamisha
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleApproveCampaign(c.id)}
                              className="text-green-600 border-green-500/30 hover:bg-green-500/10 flex items-center gap-1 mx-auto mt-1 md:mt-0"
                            >
                              <ShieldCheck className="h-4 w-4" />
                              Approve / Idhinisha
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}

          {/* TAB 3: ABUSE REPORTS */}
          {activeTab === 'abuse' && (
            <Card className="border-amber-500/10">
              <CardHeader>
                <CardTitle className="text-xl">Spam & DNC Complaints / Malalamiko ya Spam na DNC</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b bg-muted/30">
                      <th className="p-3">Recipient / Mpokeaji</th>
                      <th className="p-3">Organization / Shirika</th>
                      <th className="p-3">Complaint / Aina</th>
                      <th className="p-3">Details / Maelezo</th>
                      <th className="p-3">Status / Hali</th>
                      <th className="p-3">Reported / Tarehe</th>
                      <th className="p-3 text-center">Actions / Hatua</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reports.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-muted-foreground">
                          No abuse reports logged. / Hakuna ripoti za usumbufu.
                        </td>
                      </tr>
                    ) : (
                      reports.map((r) => (
                        <tr key={r.id} className="border-b hover:bg-muted/10 transition-colors">
                          <td className="p-3 font-mono text-xs">{r.reporter_number}</td>
                          <td className="p-3 font-semibold text-red-600">{r.tenant_name}</td>
                          <td className="p-3 capitalize text-xs">
                            <span className="bg-red-50 text-red-700 px-2 py-0.5 rounded border border-red-200">
                              {r.report_type}
                            </span>
                          </td>
                          <td className="p-3 text-xs max-w-xs truncate">{r.details || 'N/A'}</td>
                          <td className="p-3 capitalize">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                              r.status === 'pending' ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'
                            }`}>
                              {r.status}
                            </span>
                          </td>
                          <td className="p-3 text-xs text-muted-foreground">
                            {new Date(r.created_at).toLocaleString()}
                          </td>
                          <td className="p-3 text-center">
                            {r.status === 'pending' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setResolvingReport(r);
                                  setResolveStatus('resolved');
                                  setResolveNotes('');
                                  setSuspendTenant(false);
                                }}
                                className="text-red-600 border-red-500/30 hover:bg-red-500/10 flex items-center gap-1 mx-auto"
                              >
                                <AlertTriangle className="h-3.5 w-3.5" />
                                Resolve / Shughulikia
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}

          {/* TAB 4: PAYMENTS */}
          {activeTab === 'payments' && (
            <Card className="border-amber-500/10">
              <CardHeader>
                <CardTitle className="text-xl">Global M-Pesa & Card Payments / Malipo ya Global</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b bg-muted/30">
                      <th className="p-3">Reference / Kumbukumbu</th>
                      <th className="p-3">Organization / Shirika</th>
                      <th className="p-3">Type / Aina</th>
                      <th className="p-3">Method / Njia</th>
                      <th className="p-3 text-right">Amount / Kiasi</th>
                      <th className="p-3">Status / Hali</th>
                      <th className="p-3">Date / Tarehe</th>
                      <th className="p-3 text-center">Refund / Rudisha</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="p-8 text-center text-muted-foreground">
                          No transactions found. / Hakuna miamala iliyopatikana.
                        </td>
                      </tr>
                    ) : (
                      payments.map((p) => (
                        <tr key={p.id} className="border-b hover:bg-muted/10 transition-colors">
                          <td className="p-3 font-mono text-xs font-bold">{p.payment_reference}</td>
                          <td className="p-3 font-semibold">{p.tenant_name}</td>
                          <td className="p-3 capitalize text-xs">{p.transaction_type.replace('_', ' ')}</td>
                          <td className="p-3 uppercase text-xs">{p.payment_method.replace('_', ' ')}</td>
                          <td className="p-3 text-right font-semibold">
                            {p.currency} {p.amount.toLocaleString()}
                          </td>
                          <td className="p-3">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${
                              p.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : p.status === 'refunded'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {p.status}
                            </span>
                          </td>
                          <td className="p-3 text-xs text-muted-foreground">
                            {new Date(p.created_at).toLocaleDateString()}
                          </td>
                          <td className="p-3 text-center">
                            {p.status === 'completed' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRefund(p.id)}
                                className="text-red-500 border-red-500/20 hover:bg-red-500/10 flex items-center gap-1 mx-auto"
                              >
                                <Ban className="h-3.5 w-3.5" />
                                Refund / Rejesha
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}

          {/* TAB 5: TELEMETRY */}
          {activeTab === 'telemetry' && telemetry && (
            <div className="grid gap-6 md:grid-cols-2">
              {/* Telephony Card */}
              <Card className="border-amber-500/10">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Activity className="h-5 w-5 text-amber-500" />
                    Telephony Gateway Telemetry / Simu na Njia
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Active Channels / Njia Zilizopo:</span>
                    <span className="font-bold text-green-600">
                      {telemetry.telephony.active_outbound_channels} / {telemetry.telephony.max_channels_cap} channels
                    </span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Rate Limit / Kiwango cha Juu:</span>
                    <span className="font-bold">{telemetry.telephony.rate_limit_calls_per_min} calls/min</span>
                  </div>
                  <div className="flex justify-between pb-2">
                    <span className="text-muted-foreground">Success Transfers Today / Uhamisho wa Leo:</span>
                    <span className="font-bold text-kijani-600">{telemetry.telephony.successful_transfers_today} calls</span>
                  </div>
                </CardContent>
              </Card>

              {/* CRM Card */}
              <Card className="border-amber-500/10">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    CRM Sync Health / Uhusiano na Mifumo (CRM)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Salesforce Sync:</span>
                    <span className="font-bold text-green-600 uppercase">
                      {telemetry.crm_sync.salesforce_sync_status}
                    </span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">HubSpot Sync:</span>
                    <span className="font-bold text-green-600 uppercase">
                      {telemetry.crm_sync.hubspot_sync_status}
                    </span>
                  </div>
                  <div className="flex justify-between pb-2">
                    <span className="text-muted-foreground">Sync processes (24h):</span>
                    <span className="font-bold">{telemetry.crm_sync.sync_records_processed_24h} records</span>
                  </div>
                </CardContent>
              </Card>

              {/* Globals */}
              <Card className="border-amber-500/10 md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-lg">System-wide Counters / Takwimu za Mfumo Mzima</CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <p className="text-muted-foreground text-xs uppercase">Leads / Wateja</p>
                    <p className="text-2xl font-bold mt-1 text-kijani-600">
                      {telemetry.globals.total_leads_processed.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <p className="text-muted-foreground text-xs uppercase">Campaigns / Kampeni</p>
                    <p className="text-2xl font-bold mt-1 text-blue-600">
                      {telemetry.globals.total_campaigns_created.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <p className="text-muted-foreground text-xs uppercase">Abuse Reports</p>
                    <p className="text-2xl font-bold mt-1 text-red-600">
                      {telemetry.globals.total_abuse_reports_logged.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-muted/30 p-4 rounded-lg">
                    <p className="text-muted-foreground text-xs uppercase">Payments / Malipo</p>
                    <p className="text-2xl font-bold mt-1 text-amber-600">
                      {telemetry.globals.total_payment_txns_processed.toLocaleString()}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* --- DIALOG MODAL: EDIT LIMITS --- */}
      {editingOrg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <Card className="w-full max-w-md bg-background shadow-2xl border-amber-500/20">
            <CardHeader className="border-b border-amber-500/10 pb-4">
              <CardTitle className="text-lg text-amber-500 flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Modify Limits: {editingOrg.name}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              {/* Plan Type */}
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Plan Tier / Kifurushi</label>
                <select
                  value={orgPlan}
                  onChange={(e) => setOrgPlan(e.target.value)}
                  className="w-full mt-1 px-3 py-2 border rounded-lg text-sm bg-background text-foreground"
                >
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="growth">Growth</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>

              {/* Status */}
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Status / Hali</label>
                <select
                  value={orgStatus}
                  onChange={(e) => setOrgStatus(e.target.value)}
                  className="w-full mt-1 px-3 py-2 border rounded-lg text-sm bg-background text-foreground"
                >
                  <option value="active">Active / Kazi</option>
                  <option value="suspended">Suspended / Simamishwa</option>
                  <option value="cancelled">Cancelled / Ghairi</option>
                </select>
              </div>

              {/* Max Leads */}
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Max Database Leads / Wateja Ukomo</label>
                <Input
                  type="number"
                  value={orgMaxLeads}
                  onChange={(e) => setOrgMaxLeads(parseInt(e.target.value) || 0)}
                  className="mt-1"
                />
              </div>

              {/* Max Campaigns */}
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Max Campaigns / Kampeni Ukomo</label>
                <Input
                  type="number"
                  value={orgMaxCampaigns}
                  onChange={(e) => setOrgMaxCampaigns(parseInt(e.target.value) || 0)}
                  className="mt-1"
                />
              </div>

              {/* Buttons */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" size="sm" onClick={() => setEditingOrg(null)}>
                  Cancel / Ghairi
                </Button>
                <Button
                  size="sm"
                  onClick={handleUpdateOrg}
                  className="bg-amber-500 hover:bg-amber-600 text-white"
                >
                  Save Changes / Hifadhi
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* --- DIALOG MODAL: RESOLVE ABUSE --- */}
      {resolvingReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <Card className="w-full max-w-md bg-background shadow-2xl border-red-500/20">
            <CardHeader className="border-b border-red-500/10 pb-4">
              <CardTitle className="text-lg text-red-600 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Resolve Complaint / Shughulikia Malalamiko
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <p className="text-xs text-muted-foreground">
                Complaint from number <span className="font-mono font-bold text-foreground">{resolvingReport.reporter_number}</span> against organization <span className="font-bold text-red-600">{resolvingReport.tenant_name}</span>.
              </p>

              {/* Action */}
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Resolution Status / Uamuzi</label>
                <select
                  value={resolveStatus}
                  onChange={(e) => setResolveStatus(e.target.value)}
                  className="w-full mt-1 px-3 py-2 border rounded-lg text-sm bg-background text-foreground"
                >
                  <option value="resolved">Resolved / Imeshughulikiwa</option>
                  <option value="dismissed">Dismissed / Imefutiliwa mbali</option>
                </select>
              </div>

              {/* Resolution Notes */}
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Resolution Notes / Maelezo ya Uamuzi</label>
                <textarea
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                  rows={3}
                  placeholder="Enter actions taken, e.g. warned organization, deleted recipient from outbox..."
                  className="w-full mt-1 px-3 py-2 border rounded-lg text-sm bg-background text-foreground"
                />
              </div>

              {/* Suspend Tenant Checkbox */}
              <div className="flex items-center gap-3 bg-red-50 dark:bg-red-950/20 p-3 rounded-lg border border-red-200/50">
                <input
                  type="checkbox"
                  id="suspendTenant"
                  checked={suspendTenant}
                  onChange={(e) => setSuspendTenant(e.target.checked)}
                  className="h-4 w-4 text-red-600 border-gray-300 rounded focus:ring-red-500"
                />
                <label htmlFor="suspendTenant" className="text-xs font-semibold text-red-700 dark:text-red-400 select-none cursor-pointer">
                  Suspend Organization Immediately / Funga Shirika Hili Mara Moja
                </label>
              </div>

              {/* Buttons */}
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" size="sm" onClick={() => setResolvingReport(null)}>
                  Cancel / Ghairi
                </Button>
                <Button
                  size="sm"
                  onClick={handleResolveAbuse}
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  Submit / Hifadhi
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
