import { apiClient } from "./apiClient";
import { API_BASE_URL, API_VERSION } from "@/constants/api";
import { getLocaleFromPathname } from "@/utils/locale";

import type {
  LoginCredentials,
  ApiSignupData,
  ApiCompleteProfileData,
  RequestOtpFormValues,
  VerifyOtpFormValues,
  ResetPasswordFormValues,
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

// All functions below are solid. They correctly delegate to the apiClient.
// No changes are needed for most of them.

export const loginUser = (
  credentials: LoginCredentials
): Promise<LoginResponse> => {
  return apiClient<LoginResponse>("/auth/login/", {
    method: "POST",
    body: JSON.stringify(credentials),
    isPublic: true,
  });
};

export const signupUser = (data: ApiSignupData): Promise<SignupResponse> => {
  return apiClient<SignupResponse>("/auth/signup/", {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
  });
};

// ... (confirmEmail, requestOtp, verifyOtp, resetPasswordWithOtp are all fine)
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
    `/auth/confirm-email/${uidb64}/${token}/`,
    {
      method: "GET",
      isPublic: true,
    }
  );
};

export const requestOtp = (
  data: RequestOtpFormValues
): Promise<RequestOtpResponse> => {
  return apiClient<RequestOtpResponse>("/auth/password/reset/request-otp/", {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
  });
};

export const verifyOtp = (
  data: VerifyOtpFormValues
): Promise<VerifyOtpResponse> => {
  return apiClient<VerifyOtpResponse>("/auth/password/reset/verify-otp/", {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
  });
};

export const resetPasswordWithOtp = (
  data: ResetPasswordFormValues
): Promise<ResetPasswordResponse> => {
  return apiClient<ResetPasswordResponse>("/auth/password/reset/confirm-otp/", {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
  });
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

  return apiClient<UserProfile>("/users/me/complete-profile/", {
    method: "PATCH",
    body: formData, // apiClient will correctly handle FormData
  });
};

export const logoutUserApi = (payload: LogoutPayload): Promise<void> => {
  return apiClient<void>("/auth/logout/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
  const url = `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/token/refresh/`;

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
  return apiClient<UserProfile>("/users/me/");
};

export const updateUserProfile = (
  data: Partial<ApiCompleteProfileData>
): Promise<UserProfile> => {
  // Check if the payload contains a file. If so, we must use FormData.
  const hasFile = Object.values(data).some((value) => value instanceof File);

  let body: string | FormData;
  const headers: HeadersInit = {};

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
    body = JSON.stringify(data);
    headers["Content-Type"] = "application/json";
  }

  return apiClient<UserProfile>("/users/me/", {
    method: "PATCH",
    body,
    headers, // apiClient will merge/handle these correctly.
  });
};
