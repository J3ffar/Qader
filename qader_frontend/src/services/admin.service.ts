import { apiClient } from "./apiClient";
import type { PaginatedResponse } from "@/types/api";
import type { AdminUserListItem } from "@/types/api/admin.types";

// Define params type for better type-safety
interface GetAdminUsersParams {
  page?: number;
  search?: string;
  role?: string[];
  user__is_active?: boolean;
}

/**
 * Fetches a paginated list of users for the admin panel.
 * @param params - Optional query parameters for filtering and pagination.
 */
export const getAdminUsers = (params?: GetAdminUsersParams) => {
  return apiClient<PaginatedResponse<AdminUserListItem>>("/admin/users/", {
    params,
  });
};

/**
 * Deletes a user from the admin panel.
 * @param userId - The ID of the user's profile to delete.
 */
export const deleteAdminUser = (userId: number) => {
  return apiClient(`/admin/users/${userId}/`, {
    method: "DELETE",
  });
};
