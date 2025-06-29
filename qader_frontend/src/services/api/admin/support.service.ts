import { apiClient } from "@/services/apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import { queryKeys } from "@/constants/queryKeys";
import type { SupportTicketListResponse } from "@/types/api/admin/support.types";
import type { ApiRequestParams } from "@/types/api";

export const getSupportTickets = async (params: ApiRequestParams = {}) => {
  return apiClient<SupportTicketListResponse>(
    API_ENDPOINTS.ADMIN.SUPPORT.TICKETS,
    {
      params,
    }
  );
};

export const deleteSupportTicket = async (ticketId: number) => {
  return apiClient<void>(
    API_ENDPOINTS.ADMIN.SUPPORT.TICKET_DETAIL(ticketId),
    {
      method: "DELETE",
    }
  );
};
