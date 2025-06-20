import { apiClient } from "./apiClient";
import type {
  PaginatedNotificationsResponse,
  MarkReadResponse,
  UnreadNotificationsCountResponse,
  MarkNotificationsReadPayload,
} from "@/types/api/notification.types";
import { API_ENDPOINTS } from "@/constants/api";

interface GetNotificationsParams {
  page?: number;
  pageSize?: number;
  is_read?: boolean;
  ordering?: string;
}

export const getNotifications = async (
  params?: GetNotificationsParams
): Promise<PaginatedNotificationsResponse> => {
  // apiClient will handle query param conversion
  return apiClient<PaginatedNotificationsResponse>(
    API_ENDPOINTS.NOTIFICATIONS.LIST,
    { method: "GET", params }
  );
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
