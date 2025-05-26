export interface SubscriptionDetails {
  is_active: boolean;
  expires_at: string | null; // ISO date string
  // ... other subscription fields
}

export interface User {
  id: number;
  username: string; // This seems to be the identifier used for login
  email: string;
  full_name: string;
  preferred_name?: string | null;
  role: string; // e.g., "student", "admin"
  subscription: SubscriptionDetails;
  profile_picture_url?: string | null;
  level_determined: boolean;
  profile_complete: boolean;
  is_super?: boolean; // For admin checks
  is_staff?: boolean; // For staff/sub-admin checks
  points?: number;
  current_streak_days?: number;
  assigned_mentor?: any; // Define more strictly if possible
  mentees_count?: number;
  unread_notifications_count?: number;
  language?: string; // e.g., "ar"
}

export interface UserProfile extends User {
  // Assuming UserProfile has all fields of User plus potentially more
  // Add any extra fields specific to UserProfile if they exist
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface SignupResponse {
  detail: string; // e.g., "Confirmation email sent. Please check your inbox."
}

export interface ApiErrorDetail {
  // For 400 errors with field-specific messages
  [key: string]: string[] | string; // e.g. { email: ["email already exists"] } or { detail: "error message" }
}
