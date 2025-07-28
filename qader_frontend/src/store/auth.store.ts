import { create, StateCreator } from "zustand";
import { useMemo } from "react";
import type { UserProfile } from "@/types/api/auth.types";
import { logoutUserApi } from "@/services/auth.service";
import Cookies from "js-cookie";

// --- State and Actions Interfaces ---
interface AuthStateCore {
  accessToken: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isProfileComplete: boolean;
  isRefreshingToken: boolean;
}

interface AuthActions {
  login: (tokens: { access: string }, userData: UserProfile) => void;
  logout: () => Promise<void>;
  setTokens: (tokens: { access: string }) => void;
  setUser: (userData: UserProfile | null) => void;
  updateUserProfile: (updatedUserData: Partial<UserProfile>) => void;
  setIsProfileComplete: (isComplete: boolean) => void;
  setIsRefreshingToken: (isRefreshing: boolean) => void;
}

export interface AuthState extends AuthStateCore, AuthActions {}

// --- Zustand Store Implementation ---
const authStoreCreator: StateCreator<AuthState> = (set, get) => ({
  // --- Initial State ---
  accessToken: null,
  user: null,
  isAuthenticated: false,
  isProfileComplete: false,
  isRefreshingToken: false,

  // --- Actions ---
  login: (tokens, userData) => {
    set({
      accessToken: tokens.access,
      user: userData,
      isAuthenticated: true,
      isProfileComplete: userData.profile_complete,
      isRefreshingToken: false,
    });
  },

  logout: async () => {
    // 1. Call the BFF endpoint to clear the secure cookie
    try {
      await logoutUserApi();
    } catch (error) {
      console.warn(
        "Logout API call failed, but proceeding with client cleanup.",
        error
      );
    }

    Cookies.remove("qader-user-role", { path: "/" });

    // 2. Reset the client-side state
    set({
      accessToken: null,
      user: null,
      isAuthenticated: false,
      isProfileComplete: false,
      isRefreshingToken: false,
    });

    // IMPORTANT: Clear any other persisted client-side state if necessary
  },

  setTokens: (tokens) => {
    // Only sets the access token
    set({
      accessToken: tokens.access,
      isAuthenticated: !!tokens.access,
      isRefreshingToken: false,
    });
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
    set({ isProfileComplete: isComplete });
  },

  setIsRefreshingToken: (isRefreshing: boolean) => {
    set({ isRefreshingToken: isRefreshing });
  },
});

// REMOVE PERSISTENCE MIDDLEWARE ENTIRELY
export const useAuthStore = create<AuthState>()(authStoreCreator);

// The hooks `useAuthCore` and `useAuthActions` remain valid but will reflect the new state shape.
/**
 * Custom hook to select core authentication state.
 * This is optimized to prevent re-renders if the selected state hasn't changed.
 * `useMemo` ensures the returned object has a stable identity.
 */
export const useAuthCore = (): AuthStateCore => {
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isProfileComplete = useAuthStore((state) => state.isProfileComplete);
  const isRefreshingToken = useAuthStore((state) => state.isRefreshingToken);

  return useMemo(
    () => ({
      accessToken,
      user,
      isAuthenticated,
      isProfileComplete,
      isRefreshingToken,
    }),
    [accessToken, user, isAuthenticated, isProfileComplete, isRefreshingToken]
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
  );
};
