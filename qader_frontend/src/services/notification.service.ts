import { apiClient } from "./apiClient";
import type {
  PaginatedNotificationsResponse,
  MarkReadResponse,
  UnreadNotificationsCountResponse,
  MarkNotificationsReadPayload,
} from "@/types/api/notification.types";
import { API_ENDPOINTS } from "@/constants/api"; // Assuming you'll define endpoints here

interface GetNotificationsParams {
  page?: number;
  pageSize?: number;
  is_read?: boolean;
  ordering?: string; // e.g., "-created_at_iso"
}

export const getNotifications = async (
  params?: GetNotificationsParams
): Promise<PaginatedNotificationsResponse> => {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append("page", params.page.toString());
  if (params?.pageSize)
    queryParams.append("page_size", params.pageSize.toString());
  if (params?.is_read !== undefined)
    queryParams.append("is_read", String(params.is_read));
  if (params?.ordering) queryParams.append("ordering", params.ordering);

  const endpoint = `${
    API_ENDPOINTS.NOTIFICATIONS.LIST
  }?${queryParams.toString()}`;
  return apiClient<PaginatedNotificationsResponse>(endpoint, { method: "GET" });
};

export const markNotificationsAsRead = async (
  payload: MarkNotificationsReadPayload
): Promise<MarkReadResponse> => {
  return apiClient<MarkReadResponse>(API_ENDPOINTS.NOTIFICATIONS.MARK_READ, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const markAllNotificationsAsRead =
  async (): Promise<MarkReadResponse> => {
    return apiClient<MarkReadResponse>(
      API_ENDPOINTS.NOTIFICATIONS.MARK_ALL_READ,
      {
        method: "POST",
      }
    );
  };

export const getUnreadNotificationsCount =
  async (): Promise<UnreadNotificationsCountResponse> => {
    return apiClient<UnreadNotificationsCountResponse>(
      API_ENDPOINTS.NOTIFICATIONS.UNREAD_COUNT,
      {
        method: "GET",
      }
    );
  };
