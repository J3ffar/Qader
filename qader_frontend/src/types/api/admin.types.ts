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

// Type for the PATCH request body when updating a user
export interface UpdateAdminUserPayload {
  user?: {
    is_active?: boolean;
  };
  full_name?: string;
  role?: 'student' | 'teacher' | 'trainer' | 'admin' | 'sub_admin';
  // Add other editable fields here as needed
}

// Type for the detailed user profile response from GET /admin/users/{id}/
// This is a more comprehensive version of AdminUserListItem
export interface AdminUserProfile extends AdminUserListItem {
  // Add more detailed fields that are not in the list view
  gender: string | null;
  grade: string | null;
  language: string;
  profile_picture: string | null;
  // ... any other fields from the detailed endpoint
}

// Payload for creating a new user/employee via the admin panel
export interface CreateAdminUserPayload {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  full_name: string;
  role: 'student' | 'teacher' | 'trainer' | 'admin' | 'sub_admin';
  // Add other optional fields if needed, e.g., gender, grade
}
