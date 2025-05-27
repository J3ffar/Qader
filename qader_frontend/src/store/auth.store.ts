import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { User } from "@/types/api/auth.types";
import { logoutUserApi, LogoutPayload } from "@/services/auth.service"; // Import the API call

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (tokens: { access: string; refresh: string }, userData: User) => void;
  logout: () => Promise<void>; // Make logout async
  setTokens: (tokens: { access: string; refresh?: string }) => void; // refresh is optional here
  setUser: (userData: User | null) => void;
  isRefreshingToken: boolean; // To prevent multiple refresh calls
  setIsRefreshingToken: (isRefreshing: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isRefreshingToken: false,

      login: (tokens, userData) => {
        set({
          accessToken: tokens.access,
          refreshToken: tokens.refresh,
          user: userData,
          isAuthenticated: true,
          isRefreshingToken: false,
        });
        // console.log("User logged in, tokens set:", get().accessToken ? "Access OK" : "No Access", get().refreshToken ? "Refresh OK" : "No Refresh");
      },

      logout: async () => {
        const currentRefreshToken = get().refreshToken;
        const currentAccessToken = get().accessToken; // Needed for the logout API call

        if (currentRefreshToken && currentAccessToken) {
          try {
            await logoutUserApi(
              { refresh: currentRefreshToken },
              currentAccessToken
            );
            // console.log("Logout API call successful");
          } catch (error) {
            console.error("Logout API call failed:", error);
            // Decide if you want to proceed with client-side logout even if API fails
            // For now, we'll proceed to ensure user is logged out client-side
          }
        }
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
          isRefreshingToken: false,
        });
        // console.log("User logged out, tokens cleared");
        // Optionally clear other persisted user-related data from localStorage/sessionStorage
      },

      setTokens: (tokens) => {
        set((state) => ({
          accessToken: tokens.access,
          // Only update refresh token if provided, otherwise keep the existing one
          refreshToken:
            tokens.refresh !== undefined ? tokens.refresh : state.refreshToken,
          isAuthenticated: !!tokens.access, // User is authenticated if there's an access token
          isRefreshingToken: false,
        }));
        // console.log("Tokens updated:", get().accessToken ? "Access OK" : "No Access", get().refreshToken ? "Refresh OK" : "No Refresh");
      },

      setUser: (userData) => set({ user: userData }),
      setIsRefreshingToken: (isRefreshing) =>
        set({ isRefreshingToken: isRefreshing }),
    }),
    {
      name: "qader-auth-storage", // Ensure a unique name
      storage: createJSONStorage(() => localStorage),
      // Only persist necessary items. User can be re-fetched on load if needed.
      // Persisting isRefreshingToken helps across tabs if a refresh is in progress.
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user, // Persisting user can be convenient but ensure it's up-to-date
        isAuthenticated: state.isAuthenticated,
        // isRefreshingToken: state.isRefreshingToken, // Not typically persisted
      }),
      onRehydrateStorage: () => (state) => {
        // When rehydrating, if we have tokens but isAuthenticated is false, set it to true.
        // Or, if accessToken might be expired, rely on an initial fetch/check.
        if (
          state?.accessToken &&
          state?.refreshToken &&
          !state.isAuthenticated
        ) {
          state.isAuthenticated = true;
        }
        // Reset isRefreshingToken on rehydration, as a refresh process wouldn't survive a page reload.
        if (state) {
          state.isRefreshingToken = false;
        }
      },
    }
  )
);
