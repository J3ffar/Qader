'use client';

import { useEffect, ReactNode } from 'react';
import { useAuthStore } from '@/store/auth.store';

export function AuthProvider({ children }: { children: ReactNode }) {
  const { setTokens, setUser, accessToken } = useAuthStore();

  useEffect(() => {
    // Only run hydration if we don't have an access token in the store.
    // This prevents re-fetching on every navigation.
    if (!accessToken) {
      async function hydrateAuth() {
        try {
          const res = await fetch('/api/auth/me');
          if (res.ok) {
            const { access, user } = await res.json();
            setTokens({ access });
            setUser(user);
          }
        } catch (error) {
          console.error('Failed to hydrate auth state:', error);
        }
      }

      hydrateAuth();
    }
  }, [setTokens, setUser, accessToken]);

  return <>{children}</>;
}
