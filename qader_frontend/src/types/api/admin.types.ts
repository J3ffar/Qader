// This represents the nested 'user' object in the API response
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

// This represents a single user item in the paginated list
export interface AdminUserListItem {
  user_id: number; // This is the Profile ID, which we'll use for actions
  user: AdminNestedUser;
  full_name: string;
  preferred_name: string | null;
  role: "admin" | "student" | "sub_admin" | "teacher" | "trainer";
  points: number;
  is_subscribed: boolean;
  subscription_expires_at: string | null; // ISO 8601 date string
  level_determined: boolean;
  current_level_verbal: number | null;
  current_level_quantitative: number | null;
  created_at: string; // ISO 8601 date string
}
