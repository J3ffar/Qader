import { useAuthStore } from "@/store/auth.store";
import { refreshTokenApi } from "./auth.service";
import { API_BASE_URL, API_VERSION } from "@/constants/api";
import { getLocaleFromPathname } from "@/utils/locale";

interface FetchOptions extends RequestInit {
  isPublic?: boolean; // To mark routes that don't need auth
  isRetry?: boolean; // To prevent infinite retry loops for token refresh
}

let isCurrentlyRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
  options: FetchOptions;
  url: string;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      // prom.options.headers is Readonly<Headers> | string[][] | Record<string, string> | undefined
      // We need to make it mutable or reconstruct it.
      const mutableHeaders = new Headers(prom.options.headers);
      mutableHeaders.set("Authorization", `Bearer ${token}`);
      prom.resolve(
        fetch(prom.url, {
          ...prom.options,
          headers: mutableHeaders,
        })
      );
    }
  });
  failedQueue = [];
};

export const apiClient = async <T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> => {
  const { accessToken, refreshToken, setTokens, logout, setIsRefreshingToken } =
    useAuthStore.getState();
  const locale = getLocaleFromPathname() || "ar"; // Or your global locale management
  const fullUrl = `${API_BASE_URL}/${locale}/api/${API_VERSION}${endpoint}`; // Ensure endpoint starts with '/'

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };

  if (accessToken && !options.isPublic) {
    defaultHeaders["Authorization"] = `Bearer ${accessToken}`;
  }

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(fullUrl, config);

    if (!response.ok) {
      if (response.status === 401 && !options.isPublic && !options.isRetry) {
        if (!refreshToken) {
          // console.log("No refresh token, logging out");
          await logout(); // Perform full logout
          throw new Error("Session expired. Please log in again.");
        }

        if (isCurrentlyRefreshing) {
          // If a refresh is already in progress, queue this request
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject, options, url: fullUrl });
          });
        }

        isCurrentlyRefreshing = true;
        setIsRefreshingToken(true); // Update Zustand state

        try {
          // console.log("Attempting to refresh token with:", refreshToken);
          const refreshResponse = await refreshTokenApi({
            refresh: refreshToken,
          });
          setTokens({ access: refreshResponse.access }); // Update store with new access token
          // console.log("Token refreshed successfully. New access token:", refreshResponse.access);

          // Retry the original request with the new token
          const newHeaders = new Headers(config.headers);
          newHeaders.set("Authorization", `Bearer ${refreshResponse.access}`);
          processQueue(null, refreshResponse.access); // Process queued requests
          isCurrentlyRefreshing = false;
          setIsRefreshingToken(false);
          const retryResponse = await fetch(fullUrl, {
            ...config,
            headers: newHeaders,
          });
          if (!retryResponse.ok) {
            // If retry also fails, parse its error
            const retryErrorData = await retryResponse
              .json()
              .catch(() => ({ detail: "Retry failed with non-JSON response" }));
            const error = new Error(
              retryErrorData.detail ||
                `Request failed after retry: ${retryResponse.status}`
            ) as any;
            error.status = retryResponse.status;
            error.data = retryErrorData;
            if (retryResponse.status === 401) {
              // Refresh token itself might be invalid
              await logout(); // Perform full logout
            }
            throw error;
          }
          return (await retryResponse.json()) as T;
        } catch (refreshError: any) {
          // console.error("Failed to refresh token or retry original request:", refreshError);
          processQueue(refreshError, null); // Reject queued requests
          await logout(); // Logout if token refresh fails
          isCurrentlyRefreshing = false;
          setIsRefreshingToken(false);
          throw new Error(
            refreshError.message ||
              "Your session has expired. Please log in again."
          );
        }
      }

      // For other non-OK responses
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Request failed with non-JSON response" }));
      const error = new Error(
        errorData.detail ||
          `API Error: ${response.statusText || response.status}`
      ) as any;
      error.status = response.status;
      error.data = errorData;
      throw error;
    }

    // Handle 204 No Content specifically
    if (response.status === 204) {
      return {} as T; // Or undefined, depending on how you want to type this
    }

    return (await response.json()) as T;
  } catch (error) {
    // console.error("API Client Error:", error);
    throw error; // Re-throw to be caught by TanStack Query or calling function
  }
};
