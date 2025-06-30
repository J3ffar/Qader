import { apiClient } from "@/services/apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import type {
  SupportTicketListResponse,
  SupportTicketDetail,
  SupportTicketAdminUpdateRequest,
  AddReplyRequest,
  SupportTicketReply,
} from "@/types/api/admin/support.types";
import type { ApiRequestParams, PaginatedResponse } from "@/types/api";

// GET /en/api/v1/admin/support/tickets/
export const getSupportTickets = async (params: ApiRequestParams = {}) => {
  return apiClient<SupportTicketListResponse>(
    API_ENDPOINTS.ADMIN.SUPPORT.TICKETS,
    {
      params,
    }
  );
};

// GET /en/api/v1/admin/support/tickets/{id}/
export const getSupportTicketDetail = async (ticketId: number) => {
  return apiClient<SupportTicketDetail>(
    API_ENDPOINTS.ADMIN.SUPPORT.TICKET_DETAIL(ticketId)
  );
};

// PATCH /en/api/v1/admin/support/tickets/{id}/
export const updateSupportTicket = async (
  ticketId: number,
  payload: SupportTicketAdminUpdateRequest
) => {
  // The response body is a partial update, so we can type it loosely or create a specific type
  return apiClient<Partial<SupportTicketDetail>>(
    API_ENDPOINTS.ADMIN.SUPPORT.TICKET_DETAIL(ticketId),
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
};

// DELETE /en/api/v1/admin/support/tickets/{id}/
export const deleteSupportTicket = async (ticketId: number) => {
  return apiClient<void>(API_ENDPOINTS.ADMIN.SUPPORT.TICKET_DETAIL(ticketId), {
    method: "DELETE",
  });
};

// GET /en/api/v1/admin/support/tickets/{id}/replies/
export const getTicketReplies = async (ticketId: number) => {
  return apiClient<PaginatedResponse<SupportTicketReply>>(
    API_ENDPOINTS.ADMIN.SUPPORT.REPLIES(ticketId)
  );
};

// POST /en/api/v1/admin/support/tickets/{id}/replies/
export const addTicketReply = async (
  ticketId: number,
  payload: AddReplyRequest
) => {
  return apiClient<SupportTicketReply>(
    API_ENDPOINTS.ADMIN.SUPPORT.REPLIES(ticketId),
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};
