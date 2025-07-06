// src/lib/session.ts
import { cookies } from "next/headers";
import { API_ENDPOINTS, API_BASE_URL, API_VERSION } from "@/constants/api";
import { getLocaleFromPathname } from "@/utils/locale";
import type { UserProfile } from "@/types/api/auth.types";

const REFRESH_TOKEN_COOKIE_NAME = "qader-refresh-token";

// This is a server-side only helper
async function apiCallToDjango(endpoint: string, options: RequestInit) {
  const locale = getLocaleFromPathname() || "ar";
  const url = `${API_BASE_URL}/${locale}/api/${API_VERSION}${endpoint}`;
  return fetch(url, options);
}

export interface Session {
  isAuthenticated: boolean;
  user: UserProfile | null;
  accessToken: string | null;
}

/**
 * Retrieves the user session from the secure, HttpOnly refresh token cookie.
 * This function is designed to be called from Server Components.
 */
export async function getSession(): Promise<Session> {
  const refreshToken = (await cookies()).get(REFRESH_TOKEN_COOKIE_NAME)?.value;

  if (!refreshToken) {
    return { isAuthenticated: false, user: null, accessToken: null };
  }

  try {
    // 1. Use the refresh token to get a new access token from Django
    const refreshResponse = await apiCallToDjango(
      API_ENDPOINTS.AUTH.REFRESH_TOKEN,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: refreshToken }),
        // Caching this is tricky because it's time-sensitive.
        // It's safer to re-validate on each server-side render that needs it.
        cache: "no-store",
      }
    );

    if (!refreshResponse.ok) {
      console.error("Session refresh failed:", await refreshResponse.text());
      // This could happen if the refresh token is expired or invalid.
      // We should clear the cookie to prevent redirect loops in middleware.
      (await cookies()).delete(REFRESH_TOKEN_COOKIE_NAME);
      return { isAuthenticated: false, user: null, accessToken: null };
    }

    const { access: newAccessToken } = await refreshResponse.json();

    if (!newAccessToken) {
      return { isAuthenticated: false, user: null, accessToken: null };
    }

    // 2. Use the new access token to get the user's profile
    const userProfileResponse = await apiCallToDjango(API_ENDPOINTS.USERS.ME, {
      headers: {
        Authorization: `Bearer ${newAccessToken}`,
      },
      cache: "no-store", // User data should not be cached across requests
    });

    if (!userProfileResponse.ok) {
      return {
        isAuthenticated: true, // Has a valid token, but profile fetch failed
        user: null,
        accessToken: newAccessToken,
      };
    }

    const user = await userProfileResponse.json();

    return {
      isAuthenticated: true,
      user,
      accessToken: newAccessToken,
    };
  } catch (error) {
    console.error("Error in getSession:", error);
    return { isAuthenticated: false, user: null, accessToken: null };
  }
}
