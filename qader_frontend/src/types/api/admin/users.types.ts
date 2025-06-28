// Corresponds to the nested 'user' object in the API response
export interface AdminNestedUser {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string; // ISO 8601 date string
  last_login: string | null; // ISO 8601 date string
}

// Represents a single user in the paginated list from GET /admin/users/
export interface AdminUserListItem {
  user_id: number; // This is the Profile ID
  user: AdminNestedUser;
  full_name: string;
  role: "admin" | "student" | "sub_admin" | "teacher" | "trainer";
  points: number;
  is_subscribed: boolean;
  created_at: string; // ISO 8601 date string
}

// Represents the detailed user profile from GET /admin/users/{id}/
export interface AdminUserProfile extends AdminUserListItem {
  preferred_name: string | null;
  subscription_expires_at: string | null; // ISO 8601 date string
  level_determined: boolean;
  current_level_verbal: number | null;
  current_level_quantitative: number | null;
  gender: string | null;
  grade: string | null;
  language: string;
  profile_picture: string | null;
  // ... other detailed fields can be added here from the spec
}

// Payload for POST /admin/users/
export interface CreateUserPayload {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  full_name: string;
  role: "admin" | "student" | "sub_admin" | "teacher" | "trainer";
}

// Payload for PATCH /admin/users/{id}/
export interface UpdateUserPayload {
  user?: {
    username?: string;
    email?: string;
    is_active?: boolean;
  };
  full_name?: string;
  role?: "admin" | "student" | "sub_admin" | "teacher" | "trainer";
}

// Represents a single entry in a user's point transaction history
export interface PointLog {
  id: number;
  points_change: number;
  reason_code: string;
  reason_code_display: string;
  timestamp: string; // ISO 8601 date string
  content_type: number | null;
  object_id: number | null;
  description: string; // Added description field
}

// Represents a single test attempt by a user
export interface UserTestAttempt {
  attempt_id: number;
  test_type: string; // e.g., "Determine Level", "Traditional Learning"
  date: string; // ISO 8601 date string
  status: "completed" | "in_progress" | "failed";
  status_display: string; // Human-readable status
  score_percentage: number | null; // Null if not completed
}

// Paginated response for user test attempts
export interface PaginatedUserTestAttempts {
  count: number;
  next: string | null;
  previous: string | null;
  results: UserTestAttempt[];
}

// Represents a user's overall statistics
export interface UserStatistics {
  total_points: number;
  total_tests_taken: number;
  average_score: number;
  time_spent_learning_minutes: number;
  // Detailed breakdowns
  performance_trends: {
    date: string; // YYYY-MM-DD
    score: number;
  }[];
  section_performance: {
    section_name: string;
    average_score: number;
  }[];
  scores_by_test_type: {
    test_type: string;
    average_score: number;
  }[];
  time_analytics: {
    daily_average_minutes: number;
    weekly_total_minutes: number;
    monthly_total_minutes: number;
  };
}
