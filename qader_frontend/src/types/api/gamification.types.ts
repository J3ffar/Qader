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
export interface PurchasedItemResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PurchasedItem[];
}

export interface PurchasedItem {
  id: number;
  item: StoreItem;
  purchased_at: string;
}

export interface StoreItem {
  id: number;
  name: string;
  description: string;
  code_name: string;
  item_type: "avatar" | "background" | "badge" | string;
  item_type_display: string;
  image_url: string;
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
  image_url: string;
  asset_file_url: string | null; // For downloadable items
  // is_active: boolean; // Implied as only active items are listed
  // stock_available: number | null; // If applicable
}
// Response for /gamification/reward-store/ is an array of RewardStoreItem[]

// From API Docs: /users/me/ for referral code
// This is already part of UserProfile in auth.types.ts
// referral: { code: string | null; referrals_count: number; earned_free_days: number; }
export type StoreItemGamificaiton = {
  id?: number | string;
  title: string;
  desc: string;
  points: number;
  image_url?: string;
};
export type PointsDataType = { day: string; percent: number };

export type GamificationSummary = {
  current_streak: number;
};

export type PointsSummary = {
  points: number;
};

export type RewardItem = {
  id: number | string;
  name: string;
  description: string;
  cost_points: number;
  image_url?: string;
};

export type Badge = {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon_url: string;
  criteria_description: string;
  is_earned: boolean;
  earned_at: string;
};
