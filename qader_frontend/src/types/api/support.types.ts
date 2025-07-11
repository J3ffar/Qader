import type { PaginatedResponse } from ".";
import { SimpleUser } from "./user.types";

// This now reflects the dynamic choices from the new endpoint
export interface IssueTypeChoice {
  value: string;
  label: string;
}

export type TicketStatus = "open" | "pending_admin" | "pending_user" | "closed";

export interface SupportTicketList {
  id: number;
  subject: string;
  issue_type: string; // The value from IssueTypeChoice
  status: TicketStatus;
  user: SimpleUser;
  created_at: string;
  updated_at: string;
  last_reply_by: string | null;
}

export interface SupportTicketReply {
  id: number;
  user: SimpleUser;
  message: string;
  created_at: string;
}

export type OptimisticMessageStatus = "sent" | "sending" | "error";

export type OptimisticSupportTicketReply = SupportTicketReply & {
  optimistic?: boolean;
  status?: OptimisticMessageStatus;
};

export interface SupportTicketDetail extends SupportTicketList {
  description: string;
  attachment: string | null;
  closed_at: string | null;
  replies: OptimisticSupportTicketReply[];
}

export type PaginatedSupportTickets = PaginatedResponse<SupportTicketList>;

export interface CreateSupportTicketPayload {
  issue_type: string;
  subject: string;
  description: string;
  attachment?: File | null;
}

export interface AddReplyPayload {
  message: string;
}
