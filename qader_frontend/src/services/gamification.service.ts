import { apiClient } from "./apiClient";
import type {
  PaginatedDailyPointSummaryResponse,
  DailyPointSummary,
  PaginatedStudyDayLogResponse,
  StudyDayLog,
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
  const queryParams = new URLSearchParams();
  if (params?.range) queryParams.append("range", params.range);
  if (params?.startDate) queryParams.append("start_date", params.startDate);
  if (params?.endDate) queryParams.append("end_date", params.endDate);
  if (params?.page) queryParams.append("page", params.page.toString());

  // Corrected endpoint for daily points summary from original API doc
  const endpoint = `${
    API_ENDPOINTS.GAMIFICATION.DAILY_POINTS_SUMMARY
  }?${queryParams.toString()}`;
  return apiClient<PaginatedDailyPointSummaryResponse>(endpoint, {
    method: "GET",
  });
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
  const queryParams = new URLSearchParams();
  if (params?.month) queryParams.append("month", params.month.toString());
  if (params?.year) queryParams.append("year", params.year.toString());
  if (params?.date_range_after)
    queryParams.append("date_range_after", params.date_range_after);
  if (params?.date_range_before)
    queryParams.append("date_range_before", params.date_range_before);
  if (params?.page) queryParams.append("page", params.page.toString());

  const endpoint = `${
    API_ENDPOINTS.GAMIFICATION.STUDY_DAYS
  }?${queryParams.toString()}`;
  return apiClient<PaginatedStudyDayLogResponse>(endpoint, { method: "GET" });
};

export const getRewardStoreItems = async (): Promise<RewardStoreItem[]> => {
  // The API doc implies /gamification/reward-store/ returns an array directly, not paginated.
  return apiClient<RewardStoreItem[]>(API_ENDPOINTS.GAMIFICATION.REWARD_STORE, {
    method: "GET",
  });
};
