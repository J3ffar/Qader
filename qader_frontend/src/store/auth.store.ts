// src/store/auth.store.ts
import { create, StateCreator } from "zustand"; // Removed StoreApi, SetStateAction as they are not directly used now
import {
  persist,
  createJSONStorage,
  PersistOptions,
  PersistStorage,
} from "zustand/middleware";
import type { UserProfile, LogoutPayload } from "@/types/api/auth.types";
import { logoutUserApi } from "@/services/auth.service";
import { useMemo } from "react";

interface AuthStateCore {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean; // This will be derived/set based on tokens/user
  isProfileComplete: boolean; // This will be derived/set based on user
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

type PersistedAuthState = Pick<
  AuthStateCore,
  "accessToken" | "refreshToken" | "user" // Only persist these core values
  // isAuthenticated and isProfileComplete will be derived or set by actions
>;

const authStoreCreator: StateCreator<AuthState> = (set, get) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  // isAuthenticated and isProfileComplete are effectively derived or set by actions
  // Their initial values here will be overridden by rehydration or login
  isAuthenticated: false,
  isProfileComplete: false,
  isRefreshingToken: false,

  login: (tokens, userData) => {
    set({
      accessToken: tokens.access,
      refreshToken: tokens.refresh,
      user: userData,
      isAuthenticated: true, // Set explicitly on login
      isProfileComplete: userData.profile_complete, // Set explicitly on login
      isRefreshingToken: false,
    });
  },

  logout: async () => {
    const currentRefreshToken = get().refreshToken;
    if (currentRefreshToken) {
      try {
        await logoutUserApi({ refresh: currentRefreshToken });
      } catch (error) {
        console.error("Logout API call failed:", error);
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
  },

  setTokens: (tokens) => {
    set((state) => ({
      accessToken: tokens.access,
      refreshToken:
        tokens.refresh !== undefined ? tokens.refresh : state.refreshToken,
      isAuthenticated: !!tokens.access, // Derived from new access token
      isRefreshingToken: false,
      // user and isProfileComplete remain unchanged unless explicitly set by another action
    }));
  },

  setUser: (userData) => {
    set((state) => ({
      user: userData,
      // isAuthenticated should ideally be driven by tokens mostly
      // If setting user to null, and tokens are still there, user might still be "authenticated session-wise"
      // but for UI, this might be okay.
      isAuthenticated: !!(state.accessToken && userData), // Or simply !!(state.accessToken)
      isProfileComplete: userData?.profile_complete ?? false, // Derived from new user data
    }));
  },

  updateUserProfile: (updatedUserData) => {
    set((state) => {
      const newUser = state.user ? { ...state.user, ...updatedUserData } : null;
      return {
        user: newUser,
        isProfileComplete: newUser?.profile_complete ?? state.isProfileComplete, // Update if new data has it
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

const persistOptions: PersistOptions<AuthState, PersistedAuthState> = {
  name: "qader-auth-storage",
  storage: createJSONStorage(
    () => localStorage
  ) as PersistStorage<PersistedAuthState>,
  partialize: (state): PersistedAuthState => ({
    // Persist only core token and user data
    accessToken: state.accessToken,
    refreshToken: state.refreshToken,
    user: state.user,
  }),
  // onRehydrateStorage is for side effects. The merging of `PersistedAuthState`
  // into the main `AuthState` is handled by the persist middleware itself.
  // We will rely on selectors or actions to correctly set/derive isAuthenticated and isProfileComplete
  // after rehydration.
  onRehydrateStorage: () => (rehydratedState, error) => {
    if (error) {
      console.error("Failed to rehydrate auth state:", error);
      return;
    }
    if (rehydratedState) {
      // The `persist` middleware will merge `rehydratedState` (accessToken, refreshToken, user)
      // into the store. Now, we need to ensure `isAuthenticated` and `isProfileComplete`
      // reflect this rehydrated state.
      // We can trigger an update after the initial rehydration merge.
      // This is a bit of a workaround for deriving state post-rehydration.
      Promise.resolve().then(() => {
        // Ensure this runs after the current event loop tick
        useAuthStore.setState((currentState) => ({
          ...currentState, // keep existing actions and non-persisted state
          isAuthenticated: !!(
            currentState.accessToken && currentState.refreshToken
          ),
          isProfileComplete: currentState.user?.profile_complete ?? false,
        }));
      });
    }
  },
  // A simpler onRehydrateStorage if you don't need to immediately set derived state:
  // onRehydrateStorage: () => (state, error) => {
  //   if (error) console.error("Failed to rehydrate auth state:", error);
  //   // Derived state (isAuthenticated, isProfileComplete) will be calculated by selectors/hooks
  // },

  // Consider versioning if your persisted state shape changes often
  // version: 1,
  // migrate: (persistedState, version) => { ... }
};

export const useAuthStore = create<AuthState>()(
  persist(authStoreCreator, persistOptions)
);

// Custom hooks for consuming the store
export const useAuthCore = (): AuthStateCore => {
  // Select individual state pieces
  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isProfileComplete = useAuthStore((state) => state.isProfileComplete);
  const isRefreshingToken = useAuthStore((state) => state.isRefreshingToken);

  // Memoize the object. It will only re-create the object if one of these dependencies changes.
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
