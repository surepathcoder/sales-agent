export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const LEAD_STATUSES = [
  'new',
  'researching',
  'contacted',
  'engaged',
  'qualified',
  'proposal',
  'negotiating',
  'closed_won',
  'closed_lost',
] as const;

export const PLAN_FEATURES = {
  free: { leads: 50, campaigns: 2, price: 0 },
  starter: { leads: 500, campaigns: 10, price: 150000 },
  growth: { leads: 5000, campaigns: 50, price: 500000 },
  enterprise: { leads: 100000, campaigns: 1000, price: 0 },
};

export const SCRAPE_SOURCES = [
  { id: 'google_maps', label: 'Google Maps' },
  { id: 'facebook', label: 'Facebook' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'web', label: 'Web Search' },
  { id: 'brela', label: 'BRELA Registry' },
] as const;
