import { useAuthStore } from "@/store/auth.store";
import { refreshTokenApi } from "./auth.service"; // This will now use apiClient internally for its call
import { API_BASE_URL, API_VERSION } from "@/constants/api";
import { getLocaleFromPathname } from "@/utils/locale"; // Client-side locale getter
import type { ApiError, ApiErrorDetail } from "@/types/api/auth.types";

interface CustomRequestInit extends RequestInit {
  isPublic?: boolean; // To mark routes that don't need auth
  isRetry?: boolean; // Internal flag to prevent infinite retry loops for token refresh
  locale?: string; // Allow explicit locale override
}

let isCurrentlyRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
  url: string;
  options: CustomRequestInit;
}> = [];

const processQueue = (error: ApiError | null, token: string | null = null) => {
  failedQueue.forEach(async (prom) => {
    // Make this async to await fetch
    if (error) {
      prom.reject(error);
    } else if (token) {
      const mutableHeaders = new Headers(prom.options.headers);
      mutableHeaders.set("Authorization", `Bearer ${token}`);
      try {
        // Re-fetch with new token. Note: this re-fetch won't go through the apiClient's full logic again for this specific call.
        // It's a direct fetch, but that's intended here as we've just refreshed.
        const refreshedResponse = await fetch(prom.url, {
          ...prom.options,
          headers: mutableHeaders,
        });
        // Re-apply response handling logic for the retried request
        if (!refreshedResponse.ok) {
          const errorData = (await refreshedResponse.json().catch(() => ({
            detail: "Retry failed with non-JSON response",
          }))) as ApiErrorDetail;
          const retryError = new Error(
            errorData.detail ||
              `Request failed after retry: ${refreshedResponse.status}`
          ) as ApiError;
          retryError.status = refreshedResponse.status;
          retryError.data = errorData;
          if (refreshedResponse.status === 401) {
            // If still 401 after refresh, means refresh token is likely bad or user was deactivated
            useAuthStore.getState().logout(); // Perform full logout
          }
          prom.reject(retryError);
          return;
        }
        if (refreshedResponse.status === 204) {
          prom.resolve({});
          return;
        }
        const responseData = await refreshedResponse.json();
        prom.resolve(responseData);
      } catch (retryFetchError) {
        prom.reject(retryFetchError);
      }
    }
  });
  failedQueue = [];
};

export const apiClient = async <T = any>( // Default T to any if not specified
  endpoint: string,
  options: CustomRequestInit = {}
): Promise<T> => {
  const { accessToken, refreshToken } = useAuthStore.getState();
  const { logout, setTokens } = useAuthStore.getState();
  const { setIsRefreshingToken } = useAuthStore.getState();

  // Determine locale: use explicit if provided, else from pathname, else default
  const currentLocale = options.locale || getLocaleFromPathname() || "ar";
  const fullUrl = `${API_BASE_URL}/${currentLocale}/api/${API_VERSION}${
    endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  }`;

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json", // Default, can be overridden for FormData
    Accept: "application/json",
  };

  if (accessToken && !options.isPublic) {
    defaultHeaders["Authorization"] = `Bearer ${accessToken}`;
  }

  // For FormData, Content-Type should be removed to let the browser set it with boundary
  let finalHeaders = new Headers({ ...defaultHeaders, ...options.headers });
  if (options.body instanceof FormData) {
    finalHeaders.delete("Content-Type");
  }

  const config: RequestInit = {
    ...options,
    headers: finalHeaders,
  };

  try {
    const response = await fetch(fullUrl, config);

    if (!response.ok) {
      const responseCloneForError = response.clone(); // Clone for safe parsing

      if (response.status === 401 && !options.isPublic && !options.isRetry) {
        if (!refreshToken) {
          // No refresh token, logout immediately
          await logout(); // Ensure await if logout is async
          const authError = new Error(
            "Session expired. No refresh token available."
          ) as ApiError;
          authError.status = 401;
          throw authError;
        }

        if (isCurrentlyRefreshing) {
          return new Promise<T>((resolve, reject) => {
            failedQueue.push({
              resolve,
              reject,
              url: fullUrl,
              options: { ...options, isRetry: true },
            }); // Pass original options
          });
        }

        isCurrentlyRefreshing = true;
        setIsRefreshingToken(true);

        try {
          // refreshTokenApi itself should use a basic fetch or a "public" version of apiClient
          // to avoid circular dependency or re-triggering this logic.
          // For now, assuming refreshTokenApi makes a direct fetch call.
          const refreshResponse = await refreshTokenApi({
            refresh: refreshToken,
          }); // refreshTokenApi is defined in auth.service
          setTokens({ access: refreshResponse.access }); // Update store with new access token

          // Retry original request with new token
          const newHeaders = new Headers(config.headers);
          newHeaders.set("Authorization", `Bearer ${refreshResponse.access}`);

          // Process queued requests first
          processQueue(null, refreshResponse.access);

          // Then retry the current request
          const retryResponse = await fetch(fullUrl, {
            ...config,
            headers: newHeaders,
          });

          if (!retryResponse.ok) {
            const retryErrorData = (await retryResponse.json().catch(() => ({
              detail: "Request failed after retry with non-JSON response",
            }))) as ApiErrorDetail;
            const error = new Error(
              retryErrorData.detail ||
                `Request failed after retry: ${retryResponse.status}`
            ) as ApiError;
            error.status = retryResponse.status;
            error.data = retryErrorData;
            if (retryResponse.status === 401) {
              // If still 401, refresh token itself might be invalid
              await logout();
            }
            throw error;
          }
          isCurrentlyRefreshing = false;
          setIsRefreshingToken(false);
          if (retryResponse.status === 204) return {} as T;
          return (await retryResponse.json()) as T;
        } catch (refreshError: any) {
          processQueue(refreshError as ApiError, null); // Reject queued requests with the refresh error
          await logout(); // Logout if token refresh fails catastrophically
          isCurrentlyRefreshing = false;
          setIsRefreshingToken(false);
          const err = new Error(
            refreshError.message || "Session expired. Please log in again."
          ) as ApiError;
          err.status = refreshError.status || 401;
          err.data = refreshError.data;
          throw err;
        }
      }

      // For other non-OK responses (not 401 or already a retry)
      const errorData = (await responseCloneForError.json().catch(() => ({
        detail: `API Error: ${
          response.statusText || response.status
        } (Non-JSON response)`,
      }))) as ApiErrorDetail;
      const error = new Error(
        errorData.detail ||
          `API Error: ${response.statusText || response.status}`
      ) as ApiError;
      error.status = response.status;
      error.data = errorData; // Attach full error data for components to use
      throw error;
    }

    // Handle 204 No Content specifically
    if (response.status === 204) {
      return {} as T; // Or undefined, depending on how you want to type this
    }

    return (await response.json()) as T;
  } catch (error: any) {
    // Ensure the thrown error is consistently an ApiError or similar
    if (!(error.status && error.data !== undefined)) {
      const networkError = new Error(
        error.message || "Network error or request failed"
      ) as ApiError;
      // You might not have a status for true network errors (e.g., fetch itself fails)
      // networkError.status = error.status; // if available
      // networkError.data = error.data; // if available
      throw networkError;
    }
    throw error; // Re-throw to be caught by TanStack Query or calling function
  }
};
