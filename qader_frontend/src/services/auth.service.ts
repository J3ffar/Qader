import { apiClient } from "./apiClient";
import { API_ENDPOINTS, API_BASE_URL, API_VERSION } from "@/constants/api";
import { getLocaleFromPathname } from "@/utils/locale";

import type {
  LoginCredentials,
  ApiSignupData,
  ApiCompleteProfileData,
  RequestOtpFormValues,
  VerifyOtpFormValues,
  ResetPasswordFormValues,
  ChangePasswordFormValues,
} from "@/types/forms/auth.schema";
import type {
  LoginResponse,
  SignupResponse,
  UserProfile,
  RequestOtpResponse,
  VerifyOtpResponse,
  ResetPasswordResponse,
  RefreshTokenPayload,
  RefreshTokenResponse,
  LogoutPayload,
} from "@/types/api/auth.types";
import { ApiError } from "@/lib/errors"; // Import our custom error
import { useAuthStore } from "@/store/auth.store";
import { ApiUpdateUserProfileData } from "@/types/api/user.types";

// All functions below are solid. They correctly delegate to the apiClient.
// No changes are needed for most of them.

// THIS FUNCTION NOW CALLS OUR NEXT.JS BFF, NOT DJANGO DIRECTLY
export const loginUser = (
  credentials: LoginCredentials
): Promise<{ access: string; user: UserProfile }> => {
  // This is a direct fetch call to our own backend. We don't use apiClient here.
  return fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  }).then(async (res) => {
    if (!res.ok) {
      const errorData = await res.json();
      throw new ApiError(
        errorData.detail || "Login failed",
        res.status,
        errorData
      );
    }
    return res.json();
  });
};

// NEW FUNCTION FOR SESSION HYDRATION
export const getAuthSession = async (): Promise<{
  access: string;
  user: UserProfile;
}> => {
  const response = await fetch("/api/auth/me", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.error || "Session not found",
      response.status,
      errorData
    );
  }

  return response.json();
};

export const signupUser = (data: ApiSignupData): Promise<SignupResponse> => {
  return apiClient<SignupResponse>(API_ENDPOINTS.AUTH.SIGNUP, {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
    credentials: "include",
  });
};

export interface ConfirmEmailParams {
  uidb64: string;
  token: string;
}
export type ConfirmEmailResponse = LoginResponse;

export const confirmEmail = ({
  uidb64,
  token,
}: ConfirmEmailParams): Promise<ConfirmEmailResponse> => {
  return apiClient<ConfirmEmailResponse>(
    API_ENDPOINTS.AUTH.CONFIRM_EMAIL(uidb64, token),
    {
      method: "GET",
      isPublic: true,
    }
  );
};

export const requestOtp = (
  data: RequestOtpFormValues
): Promise<RequestOtpResponse> => {
  return apiClient<RequestOtpResponse>(API_ENDPOINTS.AUTH.REQUEST_OTP, {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
  });
};

export const verifyOtp = (
  data: VerifyOtpFormValues
): Promise<VerifyOtpResponse> => {
  return apiClient<VerifyOtpResponse>(API_ENDPOINTS.AUTH.VERIFY_OTP, {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
  });
};

export const resetPasswordWithOtp = (
  data: ResetPasswordFormValues
): Promise<ResetPasswordResponse> => {
  return apiClient<ResetPasswordResponse>(
    API_ENDPOINTS.AUTH.RESET_PASSWORD_CONFIRM_OTP,
    {
      method: "POST",
      body: JSON.stringify(data),
      isPublic: true,
    }
  );
};

export const completeUserProfile = (
  data: ApiCompleteProfileData
): Promise<UserProfile> => {
  const formData = new FormData();
  Object.entries(data).forEach(([key, value]) => {
    if (value instanceof File) {
      formData.append(key, value);
    } else if (value !== null && value !== undefined) {
      formData.append(key, String(value));
    }
  });

  // Default to current locale if language is not explicitly provided.
  if (!formData.has("language")) {
    formData.append("language", getLocaleFromPathname() || "ar");
  }

  return apiClient<UserProfile>(API_ENDPOINTS.USERS.COMPLETE_PROFILE, {
    method: "PATCH",
    body: formData, // apiClient will correctly handle FormData
  });
};

// THIS FUNCTION NOW CALLS OUR NEXT.JS BFF
export const logoutUserApi = async (): Promise<void> => {
  await fetch("/api/auth/logout");
  // We don't care about the response, just that we fired the request.
};

/**
 * CRITICAL: This function MUST use a direct `fetch` call and NOT the `apiClient`.
 * Using the `apiClient` here would cause an infinite loop if the refresh token
 * itself is invalid, as the client would try to refresh the token to... refresh the token.
 */
export const refreshTokenApi = async (
  payload: RefreshTokenPayload
): Promise<RefreshTokenResponse> => {
  const locale = getLocaleFromPathname() || "ar";
  const url = `${API_BASE_URL}/${locale}/api/${API_VERSION}${API_ENDPOINTS.AUTH.REFRESH_TOKEN}`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: "Token refresh failed with non-JSON response.",
    }));
    // We throw a standard error here, which will be caught and wrapped by apiClient's logic.
    const error = new Error(
      errorData.detail || `Token refresh failed: ${response.status}`
    ) as any;
    error.status = response.status;
    error.data = errorData;
    throw error;
  }

  return response.json();
};

export const getCurrentUserProfile = (): Promise<UserProfile> => {
  return apiClient<UserProfile>(API_ENDPOINTS.USERS.ME);
};

export const updateUserProfile = (
  // FIX: The function can accept EITHER a plain object OR FormData
  data: Partial<ApiUpdateUserProfileData> | FormData
): Promise<UserProfile> => {
  // Check if the payload is already FormData. If so, use it directly.
  const isFormData = data instanceof FormData;

  let body: string | FormData;
  const headers: HeadersInit = {};

  if (isFormData) {
    body = data;
  } else {
    // If it's a plain object, check for a file inside and build FormData if needed.
    const hasFile = Object.values(data).some((value) => value instanceof File);
    if (hasFile) {
      const formData = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        if (value instanceof File) {
          formData.append(key, value);
        } else if (value !== null && value !== undefined) {
          formData.append(key, String(value));
        }
      });
      body = formData;
    } else {
      // No file, so stringify the plain object.
      body = JSON.stringify(data);
      headers["Content-Type"] = "application/json";
    }
  }

  return apiClient<UserProfile>(API_ENDPOINTS.USERS.ME, {
    method: "PATCH",
    body,
    headers,
  });
};

// Assuming the API returns a simple success message
export interface ChangePasswordResponse {
  detail: string;
}

/**
 * Changes the password for the currently authenticated user.
 * @param payload - An object containing current_password, new_password, and new_password_confirm.
 * @returns A promise that resolves to the API success message.
 */
export const changePassword = (
  payload: ChangePasswordFormValues
): Promise<ChangePasswordResponse> => {
  return apiClient<ChangePasswordResponse>(
    API_ENDPOINTS.USERS.CHANGE_PASSWORD,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};
