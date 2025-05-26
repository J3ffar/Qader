import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { User } from "@/types/api/auth.types"; // Define this type based on your API response

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (tokens: { access: string; refresh: string }, userData: User) => void;
  logout: () => void;
  setTokens: (tokens: { access: string; refresh: string }) => void;
  setUser: (userData: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      login: (tokens, userData) =>
        set({
          accessToken: tokens.access,
          refreshToken: tokens.refresh,
          user: userData,
          isAuthenticated: true,
        }),
      logout: () => {
        // TODO: Call API to invalidate refresh token if your backend supports it
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        });
        // Consider removing other persisted data related to user session
      },
      setTokens: (tokens) =>
        set({ accessToken: tokens.access, refreshToken: tokens.refresh }),
      setUser: (userData) => set({ user: userData }),
    }),
    {
      name: "auth-storage", // name of the item in the storage (must be unique)
      storage: createJSONStorage(() => localStorage), // (optional) by default, 'localStorage' is used
      // Only persist tokens, user can be re-fetched or derived
      // partialize: (state) => ({ accessToken: state.accessToken, refreshToken: state.refreshToken }),
    }
  )
);
