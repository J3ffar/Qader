import { apiClient } from "@/services/apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import { PaginatedResponse } from "@/types/api";
import {
  AdminStatisticsOverview,
  CreateExportJobResponse,
  ExportJob,
  StatisticsExportParams, // This can be reused for user export format
  StatisticsOverviewParams,
} from "@/types/api/admin/statistics.types";

type JobType = "TEST_ATTEMPTS" | "USERS";

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
  page: number = 1,
  jobType?: JobType
): Promise<PaginatedResponse<ExportJob>> => {
  const params: { ordering: string; page: number; job_type?: JobType } = {
    ordering: "-created_at",
    page,
  };

  if (jobType) {
    params.job_type = jobType;
  }

  return apiClient<PaginatedResponse<ExportJob>>(
    API_ENDPOINTS.ADMIN.STATISTICS.EXPORT_JOBS,
    {
      method: "GET",
      params,
    }
  );
};

// NEW: Function to create a user data export job.
export const createUserExportJob = async (
  payload: Pick<StatisticsExportParams, "format">
): Promise<CreateExportJobResponse> => {
  return apiClient<CreateExportJobResponse>(
    API_ENDPOINTS.ADMIN.STATISTICS.EXPORT_USERS,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};
