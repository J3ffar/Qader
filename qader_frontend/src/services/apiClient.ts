import { useAuthStore } from "@/store/auth.store";
import { refreshTokenApi } from "./auth.service"; // This now uses a direct fetch
import { API_BASE_URL, API_VERSION } from "@/constants/api";
import { getLocaleFromPathname } from "@/utils/locale";
import { ApiError } from "@/lib/errors";
import type { ApiErrorDetail } from "@/types/api/auth.types";
import { appEvents } from "@/lib/events";

interface CustomRequestInit extends RequestInit {
  isPublic?: boolean;
  isRetry?: boolean;
  locale?: string;
  params?: Record<string, string | number | boolean | string[]>;
}

// These are module-level variables to manage the refresh state globally.
let isCurrentlyRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

/**
 * Processes all requests that failed due to a 401 error and were queued.
 * @param error - The error that occurred during token refresh. If null, refresh was successful.
 * @param token - The new access token if refresh was successful.
 */
const processQueue = (error: ApiError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      // The `apiClient` will be re-called by TanStack Query's retry mechanism
      // or by the original caller. We just need to resolve the promise here
      // to unblock them. The re-call will now have the new token from the store.
      // For simplicity and to avoid re-calling with old options, resolving is enough.
      // The caller (like TanStack Query) is responsible for the retry.
      // Resolving the promise lets the original call proceed.
      // NOTE: We resolve without a value, assuming the caller will retry the original function.
      prom.resolve();
    }
  });
  failedQueue = [];
};

/**
 * A robust API client with automatic token refreshing.
 * It wraps the native `fetch` API to provide a consistent interface for all API calls.
 * - Automatically adds Authorization header.
 * - Handles 401 errors by attempting to refresh the token.
 * - Queues concurrent requests during token refresh to avoid race conditions.
 * - Constructs API URLs with locale and version.
 * - Handles FormData and JSON request bodies.
 */
export const apiClient = async <T = any>(
  endpoint: string,
  options: CustomRequestInit = {}
): Promise<T> => {
  // Use a single call to getState() for efficiency and readability.
  const { accessToken, refreshToken, setTokens, logout, setIsRefreshingToken } =
    useAuthStore.getState();

  const currentLocale = options.locale || getLocaleFromPathname() || "ar";
  let baseUrl = `${API_BASE_URL}/${currentLocale}/api/${API_VERSION}${
    endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  }`;

  // Build query string from params object
  if (options.params) {
    const queryParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((item) => queryParams.append(key, String(item)));
      } else if (value !== undefined && value !== null) {
        queryParams.append(key, String(value));
      }
    });
    const queryString = queryParams.toString();
    if (queryString) {
      baseUrl += `?${queryString}`;
    }
  }

  const defaultHeaders: HeadersInit = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };

  if (accessToken && !options.isPublic) {
    defaultHeaders["Authorization"] = `Bearer ${accessToken}`;
  }

  const finalHeaders = new Headers({ ...defaultHeaders, ...options.headers });
  if (options.body instanceof FormData) {
    // Let the browser set the Content-Type for FormData, which includes the boundary.
    finalHeaders.delete("Content-Type");
  }

  const config: RequestInit = {
    ...options,
    headers: finalHeaders,
  };

  try {
    const response = await fetch(baseUrl, config);

    // If response is not OK, we need to handle it.
    if (!response.ok) {
      // The most important case: Unauthorized.
      if (response.status === 401 && !options.isPublic && !options.isRetry) {
        // If there's no refresh token, we can't recover. Logout immediately.
        if (!refreshToken) {
          await logout();
          throw new ApiError(
            "Session expired. No refresh token available.",
            401,
            { detail: "No refresh token." }
          );
        }

        // If a refresh is already in progress, queue this request and wait.
        if (isCurrentlyRefreshing) {
          return new Promise<T>((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
        }

        // Start the token refresh process.
        isCurrentlyRefreshing = true;
        setIsRefreshingToken(true);

        return new Promise<T>((resolve, reject) => {
          refreshTokenApi({ refresh: refreshToken })
            .then((refreshResponse) => {
              setTokens({ access: refreshResponse.access });
              // After successful refresh, retry the original request with the new token.
              const newHeaders = new Headers(config.headers);
              newHeaders.set(
                "Authorization",
                `Bearer ${refreshResponse.access}`
              );
              // Re-run the original fetch call
              resolve(
                apiClient(endpoint, {
                  ...options,
                  headers: Object.fromEntries(newHeaders.entries()),
                  isRetry: true, // Mark as retry to prevent infinite loops
                })
              );
              processQueue(null, refreshResponse.access);
            })
            .catch(async (refreshError) => {
              // If refresh fails, logout the user and reject all queued requests.
              appEvents.dispatch("auth:session-expired");
              await logout();
              const error = new ApiError(
                refreshError.message || "Session expired. Please log in again.",
                refreshError.status || 401,
                refreshError.data || { detail: "Token refresh failed." }
              );
              processQueue(error, null);
              reject(error);
            })
            .finally(() => {
              isCurrentlyRefreshing = false;
              setIsRefreshingToken(false);
            });
        });
      }

      // Handle other non-401 errors.
      const errorData = (await response.json().catch(() => ({
        detail: `API Error: ${response.statusText || response.status}`,
      }))) as ApiErrorDetail;

      throw new ApiError(
        errorData.detail || `Request failed with status ${response.status}`,
        response.status,
        errorData
      );
    }

    // For 204 No Content, return an empty object.
    if (response.status === 204) {
      return {} as T;
    }

    // For successful responses, parse and return the JSON body.
    return (await response.json()) as T;
  } catch (error) {
    // If the error is already our custom ApiError, just re-throw it.
    if (error instanceof ApiError) {
      throw error;
    }

    // For network errors or other exceptions, wrap them in our custom error.
    const networkError = error as Error;
    throw new ApiError(networkError.message || "A network error occurred.", 0, {
      detail: networkError.message,
    });
  }
};
