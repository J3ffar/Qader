import type { UserProfile } from "./auth.types"; // Assuming UserProfile is defined here

// From API Docs: /notifications/
export interface SimpleUserProfile {
  id: number;
  username: string;
  full_name?: string | null;
  profile_picture_url?: string | null;
}

export interface Notification {
  id: number;
  recipient: SimpleUserProfile; // Or just user ID if recipient is always the current user
  actor: SimpleUserProfile | null; // User who performed the action
  verb: string; // e.g., "earned a new badge"
  description: string | null; // Detailed text of the notification
  notification_type: string; // e.g., "BADGE_EARNED", "CHALLENGE_INVITE"
  notification_type_display: string; // e.g., "Badge Earned"
  is_read: boolean;
  read_at_iso: string | null; // ISO datetime string
  url: string | null; // URL to navigate to when clicked
  data: Record<string, any> | null; // Additional context specific to the notification type
  created_at_iso: string; // ISO datetime string
  timesince: string; // Human-readable time since creation (e.g., "2 hours ago")
}

export interface PaginatedNotificationsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Notification[];
}

export interface MarkReadResponse {
  detail: string; // e.g., "3 notification(s) marked as read."
}

// For /notifications/unread-count/
export interface UnreadNotificationsCountResponse {
  unread_count: number;
}

// For POST /notifications/mark-read/
export interface MarkNotificationsReadPayload {
  notification_ids: number[];
}
