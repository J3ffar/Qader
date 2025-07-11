// src/types/api/support.types.ts

import type { PaginatedResponse } from ".";
import { SimpleUser } from "./user.types";

export type IssueType =
  | "technical"
  | "financial"
  | "question_problem"
  | "other";
export type TicketStatus = "open" | "pending_admin" | "pending_user" | "closed";

export interface SupportTicketList {
  id: number;
  subject: string;
  issue_type: IssueType;
  status: TicketStatus;
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

export interface SupportTicketDetail extends SupportTicketList {
  description: string;
  attachment: string | null;
  closed_at: string | null;
  replies: SupportTicketReply[];
  user: SimpleUser;
}

export type PaginatedSupportTickets = PaginatedResponse<SupportTicketList>;

export interface CreateSupportTicketPayload {
  issue_type: IssueType;
  subject: string;
  description: string;
  attachment?: File | null;
}

export interface AddReplyPayload {
  message: string;
}
