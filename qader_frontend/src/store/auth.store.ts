// qader_frontend/src/store/auth.store.ts
import { create, StateCreator } from "zustand";
import { persist, createJSONStorage, PersistOptions } from "zustand/middleware";
import { useMemo } from "react";
import type { UserProfile } from "@/types/api/auth.types";
import { logoutUserApi } from "@/services/auth.service";
import { PATHS } from "@/constants/paths";
import { getLocaleFromPathname } from "@/utils/locale";

// --- State and Actions Interfaces ---
interface AuthStateCore {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isProfileComplete: boolean;
  isRefreshingToken: boolean;
}

interface AuthActions {
  login: (
    tokens: { access: string; refresh: string },
    userData: UserProfile
  ) => void;
  logout: () => Promise<void>;
  setTokens: (tokens: { access: string; refresh?: string }) => void;
  setUser: (userData: UserProfile | null) => void;
  updateUserProfile: (updatedUserData: Partial<UserProfile>) => void;
  setIsProfileComplete: (isComplete: boolean) => void; // Can keep this if needed for direct manipulation
  setIsRefreshingToken: (isRefreshing: boolean) => void;
}

export interface AuthState extends AuthStateCore, AuthActions {}

// --- Zustand Store Implementation ---
const authStoreCreator: StateCreator<AuthState> = (set, get) => ({
  // --- Initial State ---
  accessToken: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  isProfileComplete: false,
  isRefreshingToken: false,

  // --- Actions ---
  login: (tokens, userData) => {
    set({
      accessToken: tokens.access,
      refreshToken: tokens.refresh,
      user: userData,
      isAuthenticated: true,
      isProfileComplete: userData.profile_complete,
      isRefreshingToken: false,
    });
  },

  /**
   * --- LOGOUT ACTION (UPDATED & ENHANCED) ---
   */
  logout: async () => {
    const currentRefreshToken = get().refreshToken;
    if (currentRefreshToken) {
      try {
        await logoutUserApi({ refresh: currentRefreshToken });
      } catch (error) {
        console.warn(
          "Logout API call failed, proceeding with client-side cleanup.",
          error
        );
      }
    }

    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isProfileComplete: false,
      isRefreshingToken: false,
    });
    localStorage.removeItem("qader-auth-storage");
    // Use window.location.href for a hard redirect. This is crucial as it clears
    // all component state and ensures the user lands cleanly on the login page.
    const locale = getLocaleFromPathname() || "ar"; // Default to 'ar'
    window.location.href = `/${locale}${PATHS.HOME}`;
  },

  setTokens: (tokens) => {
    set((state) => ({
      accessToken: tokens.access,
      refreshToken: tokens.refresh ?? state.refreshToken,
      isAuthenticated: !!tokens.access,
      isRefreshingToken: false,
    }));
  },

  setUser: (userData) => {
    set((state) => ({
      user: userData,
      isAuthenticated: !!(state.accessToken && userData),
      isProfileComplete: userData?.profile_complete ?? false,
    }));
  },

  updateUserProfile: (updatedUserData) => {
    set((state) => {
      if (!state.user) return {};
      const newUser = { ...state.user, ...updatedUserData };
      return {
        user: newUser,
        isProfileComplete: newUser.profile_complete ?? state.isProfileComplete,
      };
    });
  },

  setIsProfileComplete: (isComplete: boolean) => {
    // If direct setting is needed
    set({ isProfileComplete: isComplete });
  },

  setIsRefreshingToken: (isRefreshing: boolean) => {
    set({ isRefreshingToken: isRefreshing });
  },
});

// --- Persistence Configuration ---
type PersistedAuthState = Pick<
  AuthStateCore,
  "accessToken" | "refreshToken" | "user"
>;

const persistOptions: PersistOptions<AuthState, PersistedAuthState> = {
  name: "qader-auth-storage",
  storage: createJSONStorage(() => localStorage),
  partialize: (state): PersistedAuthState => ({
    accessToken: state.accessToken,
    refreshToken: state.refreshToken,
    user: state.user,
  }),
  onRehydrateStorage: () => (state, error) => {
    if (error) {
      console.error("Failed to rehydrate auth state:", error);
      return;
    }
    if (state) {
      state.isAuthenticated = !!(state.accessToken && state.refreshToken);
      state.isProfileComplete = state.user?.profile_complete ?? false;
    }
  },
};

export const useAuthStore = create<AuthState>()(
  persist(authStoreCreator, persistOptions)
);

// --- CORRECTED CUSTOM HOOKS (Your original, performant pattern) ---

/**
 * Custom hook to select core authentication state.
 * This is optimized to prevent re-renders if the selected state hasn't changed.
 * `useMemo` ensures the returned object has a stable identity.
 */
export const useAuthCore = (): AuthStateCore => {
  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isProfileComplete = useAuthStore((state) => state.isProfileComplete);
  const isRefreshingToken = useAuthStore((state) => state.isRefreshingToken);

  return useMemo(
    () => ({
      accessToken,
      refreshToken,
      user,
      isAuthenticated,
      isProfileComplete,
      isRefreshingToken,
    }),
    [
      accessToken,
      refreshToken,
      user,
      isAuthenticated,
      isProfileComplete,
      isRefreshingToken,
    ]
  );
};

export const useAuthActions = (): AuthActions => {
  const login = useAuthStore((state) => state.login);
  const logout = useAuthStore((state) => state.logout);
  const setTokens = useAuthStore((state) => state.setTokens);
  const setUser = useAuthStore((state) => state.setUser);
  const updateUserProfile = useAuthStore((state) => state.updateUserProfile);
  const setIsProfileComplete = useAuthStore(
    (state) => state.setIsProfileComplete
  );
  const setIsRefreshingToken = useAuthStore(
    (state) => state.setIsRefreshingToken
  );

  return useMemo(
    () => ({
      login,
      logout,
      setTokens,
      setUser,
      updateUserProfile,
      setIsProfileComplete,
      setIsRefreshingToken,
    }),
    [
      login,
      logout,
      setTokens,
      setUser,
      updateUserProfile,
      setIsProfileComplete,
      setIsRefreshingToken,
    ]
  ); // Dependencies are stable function references
};
