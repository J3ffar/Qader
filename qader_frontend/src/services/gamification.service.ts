import { apiClient } from "./apiClient";
import type {
  PaginatedDailyPointSummaryResponse,
  PaginatedStudyDayLogResponse,
  RewardStoreItem,
} from "@/types/api/gamification.types";
import { API_ENDPOINTS } from "@/constants/api";

interface GetDailyPointsSummaryParams {
  range?: "today" | "week" | "month" | "year";
  startDate?: string; // YYYY-MM-DD
  endDate?: string; // YYYY-MM-DD
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
  date_range_after?: string; // YYYY-MM-DD
  date_range_before?: string; // YYYY-MM-DD
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
