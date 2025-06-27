import { apiClient } from "@/services/apiClient";
import type { PaginatedResponse } from "@/types/api";
import { API_ENDPOINTS } from "@/constants/api";
import type {
  AdminUserListItem,
  AdminUserProfile,
  CreateUserPayload,
  UpdateUserPayload,
  PointLog,
  PaginatedUserTestAttempts,
} from "@/types/api/admin/users.types";
import { UserStatistics } from "@/types/api/study.types";

interface GetAdminUsersParams {
  page?: number;
  search?: string;
  role?: string[];
  user__is_active?: boolean | string; // API might take "true"/"false" strings
}

export const getAdminUsers = (params?: GetAdminUsersParams) => {
  // Ensure empty params are not sent
  const cleanParams = Object.fromEntries(
    Object.entries(params || {}).filter(([, v]) => v !== "" && v != null)
  );
  return apiClient<PaginatedResponse<AdminUserListItem>>(
    API_ENDPOINTS.ADMIN.USERS.LIST,
    { params: cleanParams }
  );
};

export const getAdminUserDetail = (userId: number) => {
  return apiClient<AdminUserProfile>(API_ENDPOINTS.ADMIN.USERS.DETAIL(userId));
};

export const updateAdminUser = (userId: number, payload: UpdateUserPayload) => {
  return apiClient<AdminUserProfile>(API_ENDPOINTS.ADMIN.USERS.DETAIL(userId), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

export const createAdminUser = (payload: CreateUserPayload) => {
  // The backend returns the created user profile, so we type it.
  return apiClient<AdminUserProfile>(API_ENDPOINTS.ADMIN.USERS.LIST, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const deleteAdminUser = (userId: number) => {
  return apiClient(API_ENDPOINTS.ADMIN.USERS.DETAIL(userId), {
    method: "DELETE",
  });
};

// Adjust points for a user
export const adjustUserPoints = (
  userId: number,
  payload: { points_change: number; reason: string }
) => {
  return apiClient(API_ENDPOINTS.ADMIN.USERS.ADJUST_POINTS(userId), {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

// Fetch the point log for a user
export const getAdminUserPointLog = (userId: number) => {
  return apiClient<PaginatedResponse<PointLog>>(
    API_ENDPOINTS.ADMIN.USERS.POINT_LOG(userId)
  );
};

// Trigger a password reset for a user
export const resetUserPassword = (userId: number) => {
  return apiClient(API_ENDPOINTS.ADMIN.USERS.RESET_PASSWORD(userId), {
    method: "POST",
  });
};

// Get a user's test attempt history
export const getAdminUserTestHistory = (
  userId: number,
  params?: { page?: number }
) => {
  return apiClient<PaginatedUserTestAttempts>(
    API_ENDPOINTS.ADMIN.USERS.TEST_HISTORY(userId),
    {
      params,
    }
  );
};

// Get a user's statistics
export const getAdminUserStatistics = (userId: number) => {
  return apiClient<UserStatistics>(
    API_ENDPOINTS.ADMIN.USERS.STATISTICS(userId)
  );
};
