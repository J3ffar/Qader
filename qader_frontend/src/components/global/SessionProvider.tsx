"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/auth.store";
import { getAuthSession } from "@/services/auth.service";
import { FullScreenLoader } from "./FullScreenLoader";

export function SessionProvider({ children }: { children: React.ReactNode }) {
  // --- FIX: Select atomic state slices instead of creating a new object. ---
  // This is the idiomatic way to use Zustand and prevents infinite re-renders.
  // Each hook now subscribes to only one part of the store.
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const login = useAuthStore((state) => state.login);

  // This local state is for managing the initial hydration UI, not for app state.
  const [isHydrating, setIsHydrating] = useState(true);

  useEffect(() => {
    const hydrateSession = async () => {
      // Optimization: If the user is already authenticated (e.g., after logging in
      // and navigating), we don't need to re-fetch their session.
      if (isAuthenticated) {
        setIsHydrating(false);
        return;
      }

      try {
        // Attempt to get the session from our BFF API route.
        // This will succeed if a valid HttpOnly refresh token cookie exists.
        const { access, user } = await getAuthSession();

        // The `login` action from the store is stable, so it's safe to use in the effect.
        login({ access }, user);
      } catch (error) {
        // This is an expected and normal path for any user who is not logged in.
        // No valid session cookie was found, so we do nothing. The user remains logged out.
        // console.log("No active session found. User is a guest.");
      } finally {
        // Whether hydration succeeded or failed, the process is complete.
        // We can now safely show the application UI.
        setIsHydrating(false);
      }
    };

    hydrateSession();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // <-- This effect should ONLY run once on initial component mount.
  // We intentionally leave the dependency array empty to enforce this behavior.
  // We are checking for a server session, not reacting to client-state changes.

  if (isHydrating) {
    // While we check for a session, show a clean, full-page loader.
    // This prevents any UI flash (e.g., showing a "Login" button that then changes to "Dashboard").
    return <FullScreenLoader />;
  }

  return <>{children}</>;
}
