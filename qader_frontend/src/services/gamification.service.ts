import { API_ENDPOINTS } from "@/constants/api";
import type {
  PaginatedDailyPointSummaryResponse,
  PaginatedStudyDayLogResponse,
  PurchasedItemResponse,
  RewardStoreItem,
} from "@/types/api/gamification.types";
import { addDays, format, startOfWeek, subWeeks } from "date-fns";
import { apiClient } from "./apiClient";

interface GetDailyPointsSummaryParams {
  range?: "today" | "week" | "month" | "year";
  startDate?: string;
  endDate?: string;
  page?: number;
}

export const getDailyPointsSummary = async (
  params?: GetDailyPointsSummaryParams
): Promise<PaginatedDailyPointSummaryResponse> => {
  return apiClient<PaginatedDailyPointSummaryResponse>(
    API_ENDPOINTS.GAMIFICATION.DAILY_POINTS_SUMMARY,
    {
      method: "GET",
      params,
    }
  );
};

interface GetStudyDaysParams {
  month?: number;
  year?: number;
  date_range_after?: string;
  date_range_before?: string;
  page?: number;
}

export const getStudyDaysLog = async (
  params?: GetStudyDaysParams
): Promise<PaginatedStudyDayLogResponse> => {
  return apiClient<PaginatedStudyDayLogResponse>(
    API_ENDPOINTS.GAMIFICATION.STUDY_DAYS,
    {
      method: "GET",
      params,
    }
  );
};

export const getRewardStoreItems = async (): Promise<RewardStoreItem[]> => {
  // The API doc implies /gamification/reward-store/ returns an array directly, not paginated.
  return apiClient<RewardStoreItem[]>(API_ENDPOINTS.GAMIFICATION.REWARD_STORE, {
    method: "GET",
  });
};

// Get reward store item details by ID
export const getRewardStoreItemDetail = async (
  id: number | string
): Promise<RewardStoreItem> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.REWARD_STORE_DETAIL(id), {
    method: "GET",
  });
};

// Purchase a reward item by ID
export const purchaseRewardItem = async (
  itemId: number | string
): Promise<any> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.PURCHASE_REWARD_ITEM(itemId), {
    method: "POST",
  });
};

// Get all available badges
export const getAllBadges = async (): Promise<any[]> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.BADGES_LIST, {
    method: "GET",
  });
};

// Get badges earned by the current user
export const getMyBadges = async (): Promise<any[]> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.MY_BADGES, {
    method: "GET",
  });
};

// Get reward items purchased by the current user
export const getMyPurchasedItems = async (): Promise<PurchasedItemResponse> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.MY_ITEMS, {
    method: "GET",
  });
};

// Get the full point log history
export const getPointLog = async (): Promise<any[]> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.POINTS_LOG, {
    method: "GET",
  });
};

// Get details of a specific point log entry
export const getPointLogDetail = async (id: number | string): Promise<any> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.POINT_LOG_DETAIL(id), {
    method: "GET",
  });
};

// Get the overall points summary (not daily)
export const getPointsSummary = async (): Promise<any> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.POINTS_SUMMARY, {
    method: "GET",
  });
};

// Get the full gamification summary (streaks, totals, etc.)
export const getGamificationSummary = async (): Promise<any> => {
  return apiClient(API_ENDPOINTS.GAMIFICATION.GAMIFICATION_SUMMARY, {
    method: "GET",
  });
};
export const getDayGamificationSummary = async (date: string): Promise<any> => {
  return apiClient(
    API_ENDPOINTS.GAMIFICATION.GAMIFICATION_SUMMARY +
      `/?end_date=${date}&ordering=${date}`,
    {
      method: "GET",
    }
  );
};

// get the data by range
export type PointsData = {
  day: string;
  percent: number;
};
const arabicDays = [
  "الأحد",
  "الإثنين",
  "الثلاثاء",
  "الأربعاء",
  "الخميس",
  "الجمعة",
  "السبت",
];

// توليد تواريخ الأسبوع المحدد (weeksAgo = 0 => هذا الأسبوع، 1 => الأسبوع الماضي، إلخ)
const getWeekDates = (weeksAgo = 0): string[] => {
  const start = startOfWeek(subWeeks(new Date(), weeksAgo), {
    weekStartsOn: 0,
  }); // يبدأ من الأحد
  return Array.from({ length: 7 }).map((_, i) =>
    format(addDays(start, i), "yyyy-MM-dd")
  );
};

// الدالة النهائية: تعيد بيانات الأسبوع بالشكل المطلوب
export const fetchWeeklyPointsData = async (
  weeksAgo = 0
): Promise<PointsData[]> => {
  const weekDates = getWeekDates(weeksAgo);

  const response = await getDailyPointsSummary({ range: "week" }); // تقدر تضيف date filters لو حبيت
  const results = response.results;

  const map = new Map<string, number>();
  results.forEach((entry) => map.set(entry.date, entry.total_points));

  const formatted: PointsData[] = weekDates.map((date) => {
    const day = arabicDays[new Date(date).getDay()];
    return {
      day,
      percent: map.get(date) || 0,
    };
  });

  return formatted;
};
///from anu time

interface PointSummary {
  date: string;
  total_points: number;
}

interface PointsSummaryResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PointSummary[];
}

export const fetchPointsTotal = async (
  startDate: string,
  endDate: string
): Promise<number> => {
  const response = await apiClient<PointsSummaryResponse>(
    API_ENDPOINTS.GAMIFICATION.POINTS_SUMMARY,
    {
      method: "GET",
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    }
  );

  const total = response.results.reduce(
    (sum, entry) => sum + (entry.total_points ?? 0),
    0
  );

  return total;
};
export const getThisWeekPoints = async (): Promise<number> => {
  const res = await apiClient<PaginatedDailyPointSummaryResponse>(
    API_ENDPOINTS.GAMIFICATION.POINTS_SUMMARY,
    {
      method: "GET",
      params: {
        range: "week",
      },
    }
  );

  const total = res.results.reduce((acc, day) => acc + day.total_points, 0);
  return total;
};
