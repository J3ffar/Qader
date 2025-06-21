import type { SubscriptionDetailResponse } from "./subscription.types";

export interface SimpleUser {
  id: number;
  username: string;
  profile_picture: string | null;
}

// From API Docs (Shared Serializer)
export interface ReferralDetailResponse {
  code: string | null;
  referrals_count: number;
  earned_free_days: number;
}

// From API Docs (Shared Serializer)
export interface MentorInfoResponse {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
}

// Main User Profile structure from PATCH /users/me/
export interface UserProfile {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  is_super: boolean;
  full_name: string;
  preferred_name: string | null;
  gender: "male" | "female" | null;
  grade: string | null;
  has_taken_qiyas_before: boolean | null;
  profile_picture_url: string | null;
  role: string;
  points: number;
  unread_notifications_count: number;
  current_streak_days: number;
  longest_streak_days: number;
  last_study_activity_at: string | null;
  current_level_verbal: number | null;
  current_level_quantitative: number | null;
  level_determined: boolean;
  profile_complete: boolean;
  language: string;
  language_code: "ar" | "en" | string;
  last_visited_study_option: string | null;
  dark_mode_preference: "light" | "dark" | "system";
  dark_mode_auto_enabled: boolean;
  dark_mode_auto_time_start: string | null;
  dark_mode_auto_time_end: string | null;
  notify_reminders_enabled: boolean;
  upcoming_test_date: string | null;
  study_reminder_time: string | null;
  created_at: string;
  updated_at: string;
  subscription: SubscriptionDetailResponse;
  referral: ReferralDetailResponse;
  assigned_mentor: MentorInfoResponse | null;
  mentees_count: number | null;
}

// User type for general use, can be same as UserProfile or a subset
export type User = UserProfile;

/**
 * A comprehensive type representing all fields that can be sent
 * to the `PATCH /users/me/` endpoint.
 */
export interface ApiUpdateUserProfileData {
  // From Account Settings
  full_name?: string;
  preferred_name?: string | null;
  profile_picture?: File | null;

  // From Notifications Settings
  notify_reminders_enabled?: boolean;
  upcoming_test_date?: string | null;
  study_reminder_time?: string | null;
  dark_mode_auto_enabled?: boolean;
  dark_mode_auto_time_start?: string | null;
  dark_mode_auto_time_end?: string | null;

  // You can also add other fields from the original ApiCompleteProfileData if they can be updated later
  username?: string | null;
  language?: "ar" | "en" | string;
  gender?: "male" | "female" | "other" | "prefer_not_to_say";
  grade?: string;
  has_taken_qiyas_before?: boolean;
}
