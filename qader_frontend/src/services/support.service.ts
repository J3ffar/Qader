// src/services/support.service.ts

import { apiClient } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import type {
  AddReplyPayload,
  CreateSupportTicketPayload,
  PaginatedSupportTickets,
  SupportTicketDetail,
  SupportTicketReply,
} from "@/types/api/support.types";

export const getUserSupportTickets = (params?: object) => {
  return apiClient<PaginatedSupportTickets>(
    API_ENDPOINTS.USERS.SUPPORT.TICKETS,
    { params }
  );
};

export const getSupportTicketDetail = (id: number | string) => {
  return apiClient<SupportTicketDetail>(API_ENDPOINTS.USERS.SUPPORT.DETAIL(id));
};

export const createSupportTicket = (payload: CreateSupportTicketPayload) => {
  const formData = new FormData();
  formData.append("issue_type", payload.issue_type);
  formData.append("subject", payload.subject);
  formData.append("description", payload.description);
  if (payload.attachment) {
    formData.append("attachment", payload.attachment);
  }

  return apiClient<SupportTicketDetail>(API_ENDPOINTS.USERS.SUPPORT.TICKETS, {
    method: "POST",
    body: formData,
  });
};

export const addTicketReply = ({
  ticketId,
  payload,
}: {
  ticketId: number | string;
  payload: AddReplyPayload;
}) => {
  return apiClient<SupportTicketReply>(
    API_ENDPOINTS.USERS.SUPPORT.REPLIES(ticketId),
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};
