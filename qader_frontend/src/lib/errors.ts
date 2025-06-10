import type { ApiErrorDetail } from "@/types/api/auth.types";

/**
 * Custom error class for API-related errors.
 * This ensures that errors thrown from the apiClient have a consistent shape,
 * making them easier to handle in UI components and TanStack Query's `onError` handlers.
 */
export class ApiError extends Error {
  status: number;
  data: ApiErrorDetail;

  constructor(message: string, status: number, data: ApiErrorDetail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;

    // This is for V8 environments (like Node.js, Chrome)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }
}
