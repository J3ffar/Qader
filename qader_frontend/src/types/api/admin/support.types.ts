import { PaginatedResponse } from "@/types/api";
import { SimpleUserProfile } from "../notification.types";

export type TicketStatus = "open" | "pending_admin" | "pending_user" | "closed";
export type TicketPriority = 1 | 2 | 3; // 1: High, 2: Medium, 3: Low
export type TicketIssueType =
  | "technical"
  | "financial"
  | "question_problem"
  | "other";

export interface SupportTicket {
  id: number;
  subject: string;
  issue_type: TicketIssueType;
  status: TicketStatus;
  priority: TicketPriority;
  user: SimpleUserProfile;
  assigned_to: SimpleUserProfile | null;
  created_at: string;
  updated_at: string;
  last_reply_by: string;
}

export interface SupportTicketDetail
  extends Omit<SupportTicket, "last_reply_by"> {
  description: string;
  attachment: string | null;
  closed_at: string | null;
  replies: SupportTicketReply[];
}

export interface SupportTicketReply {
  id: number;
  user: SimpleUserProfile;
  message: string;
  is_internal_note: boolean;
  created_at: string;
}

export interface SupportTicketListResponse
  extends PaginatedResponse<SupportTicket> {}

export interface SupportTicketAdminUpdateRequest {
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_to_id?: number;
}
