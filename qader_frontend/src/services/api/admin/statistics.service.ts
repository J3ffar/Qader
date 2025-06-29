import { apiClient } from "@/services/apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import {
  AdminStatisticsOverview,
  StatisticsOverviewParams,
  StatisticsExportParams,
  ExportTaskResponse,
} from "@/types/api/admin/statistics.types";

export const getStatisticsOverview = async (
  params: StatisticsOverviewParams
): Promise<AdminStatisticsOverview> => {
  return apiClient<AdminStatisticsOverview>(
    API_ENDPOINTS.ADMIN.STATISTICS.OVERVIEW,
    {
      method: "GET",
      params,
    }
  );
};

export const exportStatistics = async (
  params: StatisticsExportParams
): Promise<ExportTaskResponse> => {
  return apiClient<ExportTaskResponse>(API_ENDPOINTS.ADMIN.STATISTICS.EXPORT, {
    method: "GET",
    params,
  });
};
