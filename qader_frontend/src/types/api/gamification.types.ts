// From API Docs: /gamification/points-summary/
export interface DailyPointSummary {
  date: string; // YYYY-MM-DD
  total_points: number;
}

export interface PaginatedDailyPointSummaryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: DailyPointSummary[];
}

// From API Docs: /gamification/study-days/
export interface StudyDayLog {
  study_date: string; // YYYY-MM-DD
}
export interface PaginatedStudyDayLogResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: StudyDayLog[];
}

// From API Docs: /gamification/reward-store/
export interface RewardStoreItem {
  id: number;
  name: string;
  description: string;
  item_type: string; // e.g., "avatar", "material", "competition_entry", "other"
  item_type_display: string;
  cost_points: number;
  image_url: string | null;
  asset_file_url: string | null; // For downloadable items
  // is_active: boolean; // Implied as only active items are listed
  // stock_available: number | null; // If applicable
}
// Response for /gamification/reward-store/ is an array of RewardStoreItem[]

// From API Docs: /users/me/ for referral code
// This is already part of UserProfile in auth.types.ts
// referral: { code: string | null; referrals_count: number; earned_free_days: number; }
