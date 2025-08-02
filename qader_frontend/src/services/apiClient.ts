import { useAuthStore } from "@/store/auth.store";
import { getAuthSession, refreshTokenApi } from "./auth.service";
import { API_BASE_URL, API_VERSION } from "@/constants/api";
import { getLocaleFromPathname } from "@/utils/locale";
import { ApiError } from "@/lib/errors";
import { appEvents } from "@/lib/events";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import type { ApiErrorDetail } from "@/types/api/auth.types";

interface CustomRequestInit extends RequestInit {
  isPublic?: boolean;
  isRetry?: boolean;
  locale?: string;
  params?: Record<string, any>;
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

export const apiClient = async <T = any>(
  endpoint: string,
  options: CustomRequestInit = {}
): Promise<T> => {
  // Get current state. The token will be the old one on first run,
  // and the new one on the retry run.
  const { accessToken } = useAuthStore.getState();

  const currentLocale = options.locale || getLocaleFromPathname() || "ar";
  let baseUrl = `${API_BASE_URL}/${currentLocale}/api/${API_VERSION}${
    endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  }`;
  if (options.params) {
    const queryParams = new URLSearchParams(
      Object.entries(options.params).flatMap(([key, value]) =>
        Array.isArray(value)
          ? value.map((v) => [key, String(v)])
          : [[key, String(value)]]
      )
    );
    const queryString = queryParams.toString();
    if (queryString) {
      baseUrl += `?${queryString}`;
    }
  }

  const defaultHeaders: HeadersInit = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  // This correctly adds the auth header using the token from the store
  if (accessToken && !options.isPublic) {
    defaultHeaders["Authorization"] = `Bearer ${accessToken}`;
  }

  const finalHeaders = new Headers({ ...defaultHeaders, ...options.headers });
  if (options.body instanceof FormData) finalHeaders.delete("Content-Type");

  const config: RequestInit = { ...options, headers: finalHeaders };

  if (
    config.body &&
    typeof config.body === "object" &&
    !(config.body instanceof FormData)
  ) {
    config.body = JSON.stringify(config.body);
    finalHeaders.set("Content-Type", "application/json"); // Ensure content-type is correct
  }

  config.headers = finalHeaders;

  try {
    const response = await fetch(baseUrl, config);

    if (!response.ok) {
      // --- START OF CORRECTED 401 HANDLING ---
      if (response.status === 401 && !options.isPublic && !options.isRetry) {
        if (isCurrentlyRefreshing) {
          // If a refresh is already in progress, queue this request
          return new Promise<T>((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
        }

        isCurrentlyRefreshing = true;
        useAuthStore.getState().setIsRefreshingToken(true);

        return getAuthSession() // Call our BFF to handle the refresh
          .then((newSession) => {
            // Our BFF succeeded! It got a new access token.
            // Update the store with the new session details.
            useAuthStore
              .getState()
              .login({ access: newSession.access }, newSession.user);

            // Unblock any other requests that were waiting.
            processQueue(null);

            // Retry the original request with the new token.
            return apiClient(endpoint, { ...options, isRetry: true });
          })
          .catch((refreshError) => {
            // This now means our HttpOnly cookie is invalid or expired.
            // The session is truly over.
            console.error(
              "Unrecoverable session error. Logging out.",
              refreshError
            );
            processQueue(refreshError);

            // Dispatch a global event and trigger a full logout.
            appEvents.dispatch("auth:session-expired");
            useAuthStore.getState().logout(); // This clears client state and calls the /api/auth/logout BFF endpoint.

            return Promise.reject(refreshError);
          })
          .finally(() => {
            isCurrentlyRefreshing = false;
            useAuthStore.getState().setIsRefreshingToken(false);
          });
      }

      const errorData = (await response
        .json()
        .catch(() => ({}))) as ApiErrorDetail;
      const errorMessage = getApiErrorMessage(
        { status: response.status, data: errorData },
        `Request failed with status ${response.status}`
      );
      throw new ApiError(errorMessage, response.status, errorData);
    }

    if (response.status === 204) return {} as T;
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = getApiErrorMessage(error, "A network error occurred.");
    throw new ApiError(
      message,
      (error as any).status || 0,
      (error as any).data || { detail: message }
    );
  }
};
