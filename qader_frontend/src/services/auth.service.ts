// src/services/auth.service.ts
import { apiClient } from "./apiClient"; // Use the main apiClient
import { API_BASE_URL, API_VERSION } from "@/constants/api"; // Keep for refreshTokenApi direct call
import { getLocaleFromPathname } from "@/utils/locale"; // Keep for refreshTokenApi direct call

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
  // ApiError, // apiClient will throw this
} from "@/types/api/auth.types";

// No need for separate handleResponse, apiClient does this.

export const loginUser = (
  credentials: LoginCredentials
): Promise<LoginResponse> => {
  return apiClient<LoginResponse>("/auth/login/", {
    method: "POST",
    body: JSON.stringify(credentials),
    isPublic: true, // Login doesn't require a pre-existing token
  });
};

export const signupUser = (data: ApiSignupData): Promise<SignupResponse> => {
  return apiClient<SignupResponse>("/auth/signup/", {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
  });
};

export interface ConfirmEmailParams {
  uidb64: string;
  token: string;
}
export type ConfirmEmailResponse = LoginResponse; // API doc says it returns LoginResponse structure

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

// UserProfile is returned by the API upon successful completion
export const completeUserProfile = (
  data: ApiCompleteProfileData
): Promise<UserProfile> => {
  const formData = new FormData();

  // Required fields
  formData.append("gender", data.gender);
  formData.append("grade", data.grade);
  formData.append(
    "has_taken_qiyas_before",
    String(data.has_taken_qiyas_before)
  );

  // Optional fields
  if (data.username) formData.append("username", data.username);
  if (data.preferred_name)
    formData.append("preferred_name", data.preferred_name);
  if (data.profile_picture)
    formData.append("profile_picture", data.profile_picture);
  if (data.serial_code) formData.append("serial_code", data.serial_code);
  if (data.referral_code_used)
    formData.append("referral_code_used", data.referral_code_used);
  if (data.language) formData.append("language", data.language);
  else {
    // Default to current UI locale if not specified in form
    const locale = getLocaleFromPathname() || "ar";
    formData.append("language", locale);
  }

  // apiClient handles token attachment. Method is PATCH according to API Doc.
  return apiClient<UserProfile>("/users/me/complete-profile/", {
    method: "PATCH", // API Doc for /users/me/complete-profile/ says PATCH
    body: formData, // apiClient will handle FormData content type
    // isPublic is false by default, so token will be attached
  });
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
  // Endpoint: /auth/password/reset/confirm-otp/
  return apiClient<ResetPasswordResponse>("/auth/password/reset/confirm-otp/", {
    method: "POST",
    body: JSON.stringify(data),
    isPublic: true,
  });
};

// For logout, API expects refresh token in body and Authorization header with access token.
// apiClient will add the Authorization header.
export const logoutUserApi = (payload: LogoutPayload): Promise<void> => {
  return apiClient<void>("/auth/logout/", {
    // Expects 204 No Content
    method: "POST",
    body: JSON.stringify(payload),
    // isPublic: false (default), token will be attached
  });
};

// CRITICAL: refreshTokenApi should NOT use the main apiClient that has refresh logic,
// to avoid infinite loops if the refresh token itself is invalid.
// It should use a direct fetch or a simplified client.
export const refreshTokenApi = async (
  payload: RefreshTokenPayload
): Promise<RefreshTokenResponse> => {
  const locale = getLocaleFromPathname() || "ar"; // Or from a global config
  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/token/refresh/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    }
  );
  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: "Refresh token failed" }));
    const error = new Error(
      errorData.detail || `Token refresh failed: ${response.status}`
    ) as any; // Cast to any for custom props
    error.status = response.status;
    error.data = errorData;
    throw error;
  }
  return response.json();
};

// Other user profile related services (can be in a user.service.ts later)
export const getCurrentUserProfile = (): Promise<UserProfile> => {
  return apiClient<UserProfile>("/users/me/");
};

export const updateUserProfile = (
  data: Partial<ApiCompleteProfileData>
): Promise<UserProfile> => {
  // Similar to completeUserProfile, decide if it's JSON or FormData
  let bodyContent: string | FormData;
  let headers: HeadersInit = {};

  if (
    data.profile_picture ||
    Object.values(data).some((val) => val instanceof File)
  ) {
    // Check if any value is a File
    const formData = new FormData();
    for (const key in data) {
      const value = data[key as keyof ApiCompleteProfileData];
      if (value !== undefined && value !== null) {
        // FormData cannot directly append boolean, convert to string
        if (typeof value === "boolean") {
          formData.append(key, String(value));
        } else {
          formData.append(key, value as string | Blob);
        }
      }
    }
    bodyContent = formData;
  } else {
    bodyContent = JSON.stringify(data);
    headers["Content-Type"] = "application/json";
  }

  return apiClient<UserProfile>("/users/me/", {
    method: "PATCH",
    body: bodyContent,
    headers, // apiClient will merge these with its defaults (and remove Content-Type for FormData)
  });
};

// Add other auth-related or user-related services here using apiClient
// e.g., changePassword, applySerialCode etc.
