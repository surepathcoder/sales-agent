'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Tenant, User } from '@/types';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  tenant: Tenant | null;
  setAuth: (data: {
    access_token: string;
    refresh_token: string;
    user: User;
    tenant: Tenant;
  }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      tenant: null,
      setAuth: (data) => {
        localStorage.setItem('kijani_token', data.access_token);
        set({
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user,
          tenant: data.tenant,
        });
      },
      logout: () => {
        localStorage.removeItem('kijani_token');
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          tenant: null,
        });
      },
    }),
    { name: 'kijani-auth' }
  )
);
