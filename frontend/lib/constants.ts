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
  free: { leads: 20, campaigns: 1, price: 0 },
  growth: { leads: 200, campaigns: 5, price: 75000 },
  enterprise: { leads: 1000, campaigns: 9999, price: 200000 },
};

export const SCRAPE_SOURCES = [
  { id: 'google_maps', label: 'Google Maps' },
  { id: 'facebook', label: 'Facebook' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'web', label: 'Web Search' },
  { id: 'brela', label: 'BRELA Registry' },
] as const;
