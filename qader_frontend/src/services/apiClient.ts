import { useAuthStore } from "@/store/auth.store";
import { refreshTokenApi } from "./auth.service";
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
  if (accessToken && !options.isPublic)
    defaultHeaders["Authorization"] = `Bearer ${accessToken}`;

  const finalHeaders = new Headers({ ...defaultHeaders, ...options.headers });
  if (options.body instanceof FormData) finalHeaders.delete("Content-Type");

  const config: RequestInit = { ...options, headers: finalHeaders };

  try {
    const response = await fetch(baseUrl, config);

    if (!response.ok) {
      // --- Start of 401 Unauthorized Handling ---
      if (response.status === 401 && !options.isPublic && !options.isRetry) {
        if (!refreshToken) {
          // No way to recover, trigger logout immediately.
          useAuthStore.getState().logout();
          // Hang the promise to let the redirect take over.
          return new Promise(() => {});
        }

        if (isCurrentlyRefreshing) {
          return new Promise<T>((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
        }

        isCurrentlyRefreshing = true;
        setIsRefreshingToken(true);

        return new Promise<T>((resolve, reject) => {
          refreshTokenApi({ refresh: refreshToken })
            .then((refreshResponse) => {
              setTokens({ access: refreshResponse.access });
              const newHeaders = new Headers(config.headers);
              newHeaders.set(
                "Authorization",
                `Bearer ${refreshResponse.access}`
              );
              resolve(
                apiClient(endpoint, {
                  ...options,
                  headers: Object.fromEntries(newHeaders.entries()),
                  isRetry: true,
                })
              );
              processQueue(null, refreshResponse.access);
            })
            .catch((refreshError) => {
              // --- CATASTROPHIC FAILURE: The redirect logic from previous answer ---
              console.error(
                "Unrecoverable session error. Refresh token failed. Initiating logout.",
                refreshError
              );
              appEvents.dispatch("auth:session-expired");
              useAuthStore.getState().logout();
              // Hang the promise to let the redirect complete without interruption.
              return new Promise(() => {});
            })
            .finally(() => {
              isCurrentlyRefreshing = false;
              setIsRefreshingToken(false);
            });
        });
      }
      // --- End of 401 Handling ---

      // Handle other non-401 errors (e.g., 400, 404, 500)
      const errorData = (await response
        .json()
        .catch(() => ({}))) as ApiErrorDetail;
      // CHANGE: Use your purpose-built error message parser.
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
    // CHANGE: Use your parser for network errors or other exceptions too.
    const message = getApiErrorMessage(error, "A network error occurred.");
    throw new ApiError(
      message,
      (error as any).status || 0,
      (error as any).data || { detail: message }
    );
  }
};
