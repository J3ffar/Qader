import { apiClient } from "./apiClient";
import type { PaginatedResponse } from "@/types/api";
import type {
  AdminUserListItem,
  AdminUserProfile,
  UpdateAdminUserPayload,
} from "@/types/api/admin.types";
import { API_ENDPOINTS } from "@/constants/api";

interface GetAdminUsersParams {
  page?: number;
  search?: string;
  role?: string[];
  user__is_active?: boolean;
}

export const getAdminUsers = (params?: GetAdminUsersParams) => {
  return apiClient<PaginatedResponse<AdminUserListItem>>(
    API_ENDPOINTS.ADMIN.USERS.LIST,
    {
      params,
    }
  );
};

/**
 * Fetches detailed profile information for a single user.
 * @param userId - The ID of the user's profile.
 */
export const getAdminUserDetail = (userId: number) => {
  return apiClient<AdminUserProfile>(API_ENDPOINTS.ADMIN.USERS.DETAIL(userId));
};

/**
 * Updates a user's profile information.
 * @param userId - The ID of the user's profile to update.
 * @param payload - The data to update.
 */
export const updateAdminUser = (
  userId: number,
  payload: UpdateAdminUserPayload
) => {
  return apiClient<AdminUserProfile>(API_ENDPOINTS.ADMIN.USERS.DETAIL(userId), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

/**
 * Deletes a user from the admin panel.
 * @param userId - The ID of the user's profile to delete.
 */
export const deleteAdminUser = (userId: number) => {
  return apiClient(API_ENDPOINTS.ADMIN.USERS.DETAIL(userId), {
    method: "DELETE",
  });
};
