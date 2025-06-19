// From API Docs for GET /users/subscription-plans/
export interface SubscriptionPlan {
  id: string; // e.g., "1_month"
  name: string;
  description: string;
  duration_days: number;
  requires_code_type: string; // e.g., "1_month"
}

// From API Docs (Shared Serializer)
export interface SubscriptionDetailResponse {
  is_active: boolean;
  expires_at: string | null; // ISO date string
  serial_code: string | null;
  account_type: string;
  plan_name: string | null;
  account_type_key: string | null;
  plan_identifier_key: string | null;
}
