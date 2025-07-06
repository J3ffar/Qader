'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/auth.store';

export function AuthHydrator() {
  const { setTokens, setUser } = useAuthStore();

  useEffect(() => {
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
  }, [setTokens, setUser]);

  return null;
}
