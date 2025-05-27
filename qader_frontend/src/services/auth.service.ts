import { API_BASE_URL, API_VERSION } from "@/constants/api";
import {
  LoginCredentials,
  ApiSignupData,
  ApiCompleteProfileData,
  RequestOtpFormValues,
  VerifyOtpFormValues,
  ResetPasswordFormValues,
} from "@/types/forms/auth.schema"; // We will define these schemas
import {
  LoginResponse,
  SignupResponse,
  ApiErrorDetail,
  UserProfile,
} from "@/types/api/auth.types";
import { getLocaleFromPathname } from "@/utils/locale"; // Helper to get locale

// Helper function to handle API errors
async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type");
  let data;

  if (contentType && contentType.includes("application/json")) {
    data = await response.json();
  } else {
    // Handle non-JSON responses if necessary, or assume error if not JSON
    if (!response.ok) {
      throw new Error(
        response.statusText || `HTTP error! status: ${response.status}`
      );
    }
    return {} as T; // Or handle appropriately
  }

  if (!response.ok) {
    // Attempt to parse error details from backend
    const errorData = data as ApiErrorDetail;
    let errorMessage = "An unexpected error occurred.";
    if (errorData.detail && typeof errorData.detail === "string") {
      errorMessage = errorData.detail;
    } else if (Object.keys(errorData).length > 0) {
      // Grab the first field error if available
      const firstKey = Object.keys(errorData)[0];
      const firstError = errorData[firstKey];
      if (Array.isArray(firstError) && firstError.length > 0) {
        errorMessage = `${firstKey}: ${firstError[0]}`;
      } else if (typeof firstError === "string") {
        errorMessage = `${firstKey}: ${firstError}`;
      }
    }
    const error = new Error(errorMessage) as any;
    error.status = response.status;
    error.data = errorData; // Attach full error data
    throw error;
  }
  return data as T;
}

export const loginUser = async (
  credentials: LoginCredentials
): Promise<LoginResponse> => {
  const locale = getLocaleFromPathname() || "ar"; // Get current locale
  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/login/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(credentials), // Zod schema ensures username is present
    }
  );
  return handleResponse<LoginResponse>(response);
};

export const signupUser = async (
  data: ApiSignupData
): Promise<SignupResponse> => {
  const locale = getLocaleFromPathname() || "ar";
  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/signup/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(data),
    }
  );
  return handleResponse<SignupResponse>(response);
};

export interface ConfirmEmailParams {
  uidb64: string;
  token: string;
}

// The response from confirm-email is the same as LoginResponse
export type ConfirmEmailResponse = LoginResponse;

export const confirmEmail = async ({
  uidb64,
  token,
}: ConfirmEmailParams): Promise<ConfirmEmailResponse> => {
  const locale = getLocaleFromPathname() || "ar"; // Or however you determine current locale for API calls
  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/confirm-email/${uidb64}/${token}/`,
    {
      method: "GET", // As per API docs
      headers: {
        "Content-Type": "application/json", // Though GET usually doesn't have a body, it's good practice
        Accept: "application/json",
      },
    }
  );
  return handleResponse<ConfirmEmailResponse>(response); // Re-use your existing robust handler
};

export const completeUserProfile = async (
  data: ApiCompleteProfileData,
  accessToken: string // Token needs to be passed
): Promise<UserProfile> => {
  // API returns UserProfile object
  const locale = getLocaleFromPathname() || "ar";
  const formData = new FormData();

  // Append fields to FormData
  // Required fields
  formData.append("gender", data.gender);
  formData.append("grade", data.grade);
  formData.append(
    "has_taken_qiyas_before",
    String(data.has_taken_qiyas_before)
  ); // Convert boolean to string
  formData.append("language", data.language || locale);

  // Optional fields
  if (data.preferred_name) {
    formData.append("preferred_name", data.preferred_name);
  }
  if (data.profile_picture) {
    // data.profile_picture is File | null
    formData.append("profile_picture", data.profile_picture);
  }
  if (data.serial_code) {
    formData.append("serial_code", data.serial_code);
  }
  if (data.referral_code_used) {
    formData.append("referral_code_used", data.referral_code_used);
  }

  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/users/me/complete-profile/`,
    {
      method: "PUT", // API Doc says PUT or PATCH. Let's use PUT as it replaces the profile subset.
      // Check with backend if PATCH is preferred (sends only changed fields). Your current API doc title says PATCH.
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json", // Even with FormData, backend might respond with JSON
        // 'Content-Type' is NOT set here for FormData; the browser sets it with the correct boundary
      },
      body: formData,
    }
  );
  return handleResponse<UserProfile>(response);
};

export interface RequestOtpResponse {
  detail: string;
}
export const requestOtp = async (
  data: RequestOtpFormValues
): Promise<RequestOtpResponse> => {
  const locale = getLocaleFromPathname() || "ar";
  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/password/reset/request-otp/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(data),
    }
  );
  return handleResponse<RequestOtpResponse>(response);
};

export interface VerifyOtpResponse {
  reset_token: string;
  detail: string;
}
export const verifyOtp = async (
  data: VerifyOtpFormValues
): Promise<VerifyOtpResponse> => {
  const locale = getLocaleFromPathname() || "ar";
  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/password/reset/verify-otp/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(data),
    }
  );
  return handleResponse<VerifyOtpResponse>(response);
};

export interface ResetPasswordResponse {
  detail: string;
}
export const resetPasswordWithOtp = async (
  data: ResetPasswordFormValues
): Promise<ResetPasswordResponse> => {
  const locale = getLocaleFromPathname() || "ar";
  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/password/reset/confirm-otp/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(data),
    }
  );
  return handleResponse<ResetPasswordResponse>(response);
};

export interface LogoutPayload {
  refresh: string;
}
// Logout API returns 204 No Content, so no specific response type needed beyond success/failure
export const logoutUserApi = async (
  payload: LogoutPayload,
  accessToken: string
): Promise<void> => {
  const locale = getLocaleFromPathname() || "ar";
  const response = await fetch(
    `${API_BASE_URL}/${locale}/api/${API_VERSION}/auth/logout/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        Authorization: `Bearer ${accessToken}`, // Logout itself might require auth
      },
      body: JSON.stringify(payload),
    }
  );
  // For 204 No Content, handleResponse might need adjustment if it expects JSON
  // Let's create a specific handler for 204 or modify handleResponse
  if (!response.ok) {
    // Attempt to parse error details from backend if not 204
    const contentType = response.headers.get("content-type");
    let errorData: ApiErrorDetail | null = null;
    if (contentType && contentType.includes("application/json")) {
      errorData = await response.json();
    }

    let errorMessage =
      errorData?.detail ||
      `Logout failed: ${response.statusText || response.status}`;
    if (
      typeof errorData?.detail !== "string" &&
      errorData &&
      Object.keys(errorData).length > 0
    ) {
      // Handle cases where detail might be an object of field errors, though unlikely for logout
      const firstKey = Object.keys(errorData)[0];
      const firstError = errorData[firstKey];
      errorMessage = Array.isArray(firstError)
        ? `${firstKey}: ${firstError[0]}`
        : `${firstKey}: ${firstError}`;
    }

    const error = new Error(errorMessage[0]) as any;
    error.status = response.status;
    error.data = errorData;
    throw error;
  }
  // If response.ok and status is 204, it's a success, return void
};

export interface RefreshTokenPayload {
  refresh: string;
}
export interface RefreshTokenResponse {
  access: string;
}
export const refreshTokenApi = async (
  payload: RefreshTokenPayload
): Promise<RefreshTokenResponse> => {
  const locale = getLocaleFromPathname() || "ar";
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
  return handleResponse<RefreshTokenResponse>(response); // Existing handleResponse should work if it expects JSON
};
