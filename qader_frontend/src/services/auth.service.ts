import { API_BASE_URL, API_VERSION } from "@/constants/api";
import { LoginCredentials, ApiSignupData } from "@/types/forms/auth.schema"; // We will define these schemas
import {
  LoginResponse,
  SignupResponse,
  ApiErrorDetail,
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
