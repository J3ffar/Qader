// From API Docs: Shared Serializer Structures
export interface SubscriptionDetailResponse {
  is_active: boolean;
  expires_at: string | null; // ISO date string
  serial_code: string | null;
  account_type: string; // e.g., "Free Trial", "Subscribed"
}

export interface ReferralDetailResponse {
  code: string | null;
  referrals_count: number;
  earned_free_days: number;
}

export interface MentorInfoResponse {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string; // e.g., "TEACHER", "TRAINER"
}

// Main User Profile structure (matches PATCH /users/me/ response)
export interface UserProfile {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  is_super: boolean; // Superuser
  full_name: string;
  preferred_name: string | null;
  gender: "male" | "female" | null;
  grade: string | null;
  has_taken_qiyas_before: boolean | null;
  profile_picture_url: string | null;
  role: string; // e.g., "STUDENT", "ADMIN", "TEACHER"
  points: number;
  unread_notifications_count: number;
  current_streak_days: number;
  longest_streak_days: number; // Added based on likely profile data
  last_study_activity_at: string | null; // ISO datetime string
  current_level_verbal: number | null;
  current_level_quantitative: number | null;
  level_determined: boolean;
  profile_complete: boolean;
  language: string; // Display name, e.g., "English"
  language_code: "ar" | "en" | string; // Language code
  last_visited_study_option: string | null;
  dark_mode_preference: "light" | "dark" | "system";
  dark_mode_auto_enabled: boolean;
  dark_mode_auto_time_start: string | null; // HH:MM:SS or HH:MM
  dark_mode_auto_time_end: string | null; // HH:MM:SS or HH:MM
  notify_reminders_enabled: boolean;
  upcoming_test_date: string | null; // YYYY-MM-DD
  study_reminder_time: string | null; // HH:MM:SS or HH:MM
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
  subscription: SubscriptionDetailResponse;
  referral: ReferralDetailResponse;
  assigned_mentor: MentorInfoResponse | null;
  mentees_count: number | null; // If user is a teacher/trainer
}

// User type for general use, can be same as UserProfile or a subset
export type User = UserProfile;

// For /auth/login/ and /auth/confirm-email/
export interface LoginResponse {
  access: string;
  refresh: string;
  user: UserProfile; // API doc indicates a full user object similar to UserProfile
}

// For /auth/signup/
export interface SignupResponse {
  detail: string; // e.g., "Confirmation email sent. Please check your inbox."
}

// For /auth/token/refresh/
export interface RefreshTokenPayload {
  refresh: string;
}
export interface RefreshTokenResponse {
  access: string;
}

// For /auth/logout/
export interface LogoutPayload {
  refresh: string;
}
// Logout returns 204 No Content, so no specific response body type needed.

// For /auth/password/reset/request-otp/
export interface RequestOtpResponse {
  detail: string;
}

// For /auth/password/reset/verify-otp/
export interface VerifyOtpResponse {
  reset_token: string;
  detail: string;
}

// For /auth/password/reset/confirm-otp/
export interface ResetPasswordResponse {
  detail: string;
}

// For /users/me/apply-serial-code/
export interface ApplySerialCodeResponse {
  subscription: SubscriptionDetailResponse; // API doc shows updated SubscriptionDetail object
}

// For /users/me/subscription/cancel/
export interface CancelSubscriptionResponse {
  detail: string;
  subscription: SubscriptionDetailResponse;
}

// API Error Structure
// For 400 errors with field-specific messages or a general detail message
export interface ApiErrorDetail {
  detail?: string; // General error message
  [key: string]: string[] | string | undefined; // Field-specific errors, e.g., { email: ["email already exists"] }
}

// Custom error type that API client might throw
export interface ApiError extends Error {
  status?: number;
  data?: ApiErrorDetail;
}
