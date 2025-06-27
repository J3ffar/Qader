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
