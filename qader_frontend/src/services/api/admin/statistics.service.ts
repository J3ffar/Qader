import { apiClient } from "@/services/apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import {
  AdminStatisticsOverview,
  StatisticsOverviewParams,
  StatisticsExportParams,
  CreateExportJobResponse,
  ExportJob,
} from "@/types/api/admin/statistics.types";
import { PaginatedResponse } from "@/types/api";

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

// CORRECTED: This should be a POST request to create a job.
export const createExportJob = async (
  payload: StatisticsExportParams
): Promise<CreateExportJobResponse> => {
  return apiClient<CreateExportJobResponse>(
    API_ENDPOINTS.ADMIN.STATISTICS.EXPORT_JOBS,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const getExportJobs = async (
  page: number = 1
): Promise<PaginatedResponse<ExportJob>> => {
  return apiClient<PaginatedResponse<ExportJob>>(
    API_ENDPOINTS.ADMIN.STATISTICS.EXPORT_JOBS,
    {
      method: "GET",
      params: {
        ordering: "-created_at",
        page,
        job_type: "TEST_ATTEMPTS",
      },
    }
  );
};
