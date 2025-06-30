import { PaginatedResponse } from "@/types/api";

// A standardized, reusable User object based on the API docs
export interface SimpleUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  preferred_name: string | null;
  profile_picture_url: string | null;
}

export type TicketStatus = "open" | "pending_admin" | "pending_user" | "closed";
export type TicketPriority = 1 | 2 | 3; // 1: High, 2: Medium, 3: Low
export type TicketIssueType =
  | "technical"
  | "question_problem"
  | "suggestion"
  | "inquiry"
  | "other";

// Corresponds to the `SupportTicketList` object in the API response
export interface SupportTicketListItem {
  id: number;
  subject: string;
  issue_type: TicketIssueType;
  status: TicketStatus;
  priority: TicketPriority;
  user: SimpleUser;
  assigned_to: SimpleUser | null;
  created_at: string;
  updated_at: string;
  last_reply_by: string;
}

// Corresponds to the `SupportTicketReply` object
export interface SupportTicketReply {
  id: number;
  user: SimpleUser;
  message: string;
  is_internal_note: boolean;
  created_at: string;
}

// Corresponds to the `SupportTicketDetail` object
export interface SupportTicketDetail
  extends Omit<SupportTicketListItem, "last_reply_by"> {
  description: string;
  attachment: string | null;
  closed_at: string | null;
  replies: SupportTicketReply[];
}

// Response for the list endpoint
export interface SupportTicketListResponse
  extends PaginatedResponse<SupportTicketListItem> {}

// Payload for PATCH /admin/support/tickets/{id}/
export interface SupportTicketAdminUpdateRequest {
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_to_id?: number;
}

// Payload for POST /admin/support/tickets/{id}/replies/
// MODIFIED: Added is_internal_note
export interface AddReplyRequest {
  message: string;
  is_internal_note: boolean;
}
