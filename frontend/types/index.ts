export type PlanType = 'free' | 'starter' | 'growth' | 'enterprise';
export type LeadStatus =
  | 'new'
  | 'researching'
  | 'contacted'
  | 'engaged'
  | 'qualified'
  | 'proposal'
  | 'negotiating'
  | 'closed_won'
  | 'closed_lost'
  | 'nurture';
export type LeadPriority = 'hot' | 'warm' | 'cold';

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  phone: string;
  role: string;
  nida_verified: boolean;
  language_preference: string;
  created_at: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan_type: PlanType;
  industry_vertical: string;
  billing_currency: string;
  status: string;
  settings: Record<string, unknown>;
  created_at: string;
}

export interface Lead {
  id: string;
  tenant_id: string;
  company_name: string;
  trading_name?: string;
  source: string;
  status: LeadStatus;
  lead_score: number;
  priority: LeadPriority;
  assigned_to?: string;
  tags: string[];
  address?: string;
  ai_insights: Record<string, unknown>;
  contact_count: number;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  campaign_type: string;
  status: string;
  total_leads: number;
  contacted_count: number;
  engaged_count: number;
  qualified_count: number;
  converted_count: number;
}

export interface TargetCriteria {
  industries: string[];
  locations: string[];
  company_sizes: string[];
  min_lead_score: number;
  max_results: number;
  sources: string[];
  search_query?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
