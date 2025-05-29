// src/store/auth.store.ts
import { create } from "zustand";
import { persist, createJSONStorage, PersistOptions } from "zustand/middleware";
import type { UserProfile, LogoutPayload } from "@/types/api/auth.types"; // Use UserProfile
import { logoutUserApi } from "@/services/auth.service"; // This service will use apiClient

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isProfileComplete: boolean; // New state based on user.profile_complete
  actions: {
    // Group actions for better organization
    login: (
      tokens: { access: string; refresh: string },
      userData: UserProfile
    ) => void;
    logout: () => Promise<void>;
    setTokens: (tokens: { access: string; refresh?: string }) => void;
    setUser: (userData: UserProfile | null) => void;
    updateUserProfile: (updatedUserData: Partial<UserProfile>) => void; // For partial updates after profile edit
    setIsProfileComplete: (isComplete: boolean) => void;
  };
  // Transient state, should not be persisted
  isRefreshingToken: boolean;
  setIsRefreshingToken: (isRefreshing: boolean) => void;
}

type AuthPersist = (
  config: (set: any, get: any, api: any) => AuthState,
  options: PersistOptions<AuthState, Partial<AuthState>>
) => (set: any, get: any, api: any) => AuthState;

export const useAuthStore = create<AuthState>(
  (persist as AuthPersist)(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isProfileComplete: false,
      isRefreshingToken: false, // Initial state

      actions: {
        login: (tokens, userData) => {
          set({
            accessToken: tokens.access,
            refreshToken: tokens.refresh,
            user: userData,
            isAuthenticated: true,
            isProfileComplete: userData.profile_complete,
            isRefreshingToken: false, // Reset on login
          });
          // Consider redirecting or other side effects here or in the calling component
        },

        logout: async () => {
          const currentRefreshToken = get().refreshToken;
          // const currentAccessToken = get().accessToken; // apiClient will handle adding this

          if (currentRefreshToken) {
            try {
              // logoutUserApi should ideally use the apiClient which handles token internally
              await logoutUserApi({ refresh: currentRefreshToken });
            } catch (error) {
              console.error("Logout API call failed:", error);
              // Client-side logout should proceed regardless of API failure
            }
          }
          set({
            accessToken: null,
            refreshToken: null,
            user: null,
            isAuthenticated: false,
            isProfileComplete: false,
            isRefreshingToken: false, // Reset on logout
          });
          // Clear other potentially sensitive persisted data if necessary
          // e.g. queryClient.clear(); if using TanStack Query
        },

        setTokens: (tokens) => {
          set((state) => ({
            accessToken: tokens.access,
            refreshToken:
              tokens.refresh !== undefined
                ? tokens.refresh
                : state.refreshToken,
            isAuthenticated: !!tokens.access,
            isRefreshingToken: false, // Typically reset after tokens are set
          }));
        },

        setUser: (userData) => {
          set({
            user: userData,
            isProfileComplete: userData?.profile_complete ?? false,
          });
        },
        updateUserProfile: (updatedUserData) => {
          set((state) => ({
            user: state.user ? { ...state.user, ...updatedUserData } : null,
            isProfileComplete:
              updatedUserData.profile_complete !== undefined
                ? updatedUserData.profile_complete
                : state.isProfileComplete,
          }));
        },
        setIsProfileComplete: (isComplete: boolean) => {
          set({ isProfileComplete: isComplete });
        },
      },
      setIsRefreshingToken: (isRefreshing) =>
        set({ isRefreshingToken: isRefreshing }),
    }),
    {
      name: "qader-auth-storage",
      storage: createJSONStorage(() => localStorage), // Or sessionStorage
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        isProfileComplete: state.isProfileComplete,
        // DO NOT persist isRefreshingToken as it's a transient state
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // If rehydrating with tokens, ensure isAuthenticated is true.
          // A more robust check would be to verify token validity on app load.
          state.isAuthenticated = !!(state.accessToken && state.refreshToken);
          state.isProfileComplete = state.user?.profile_complete ?? false;
          // isRefreshingToken should always be false on rehydration
          // as a refresh process would not survive a page reload.
          // This is handled by its initial state and not being in partialize.
        }
      },
    }
  )
);

// Custom hook for easier access to state and actions
export const useAuth = () => useAuthStore((state) => state);
export const useAuthActions = () => useAuthStore((state) => state.actions);
