import { apiClient } from "./apiClient";
import {
  PaginatedLearningSections,
  LearningSection,
} from "@/types/api/learning.types";
import { API_ENDPOINTS } from "@/constants/api";

export const getLearningSections = async (params?: {
  ordering?: string;
  page?: number;
}): Promise<PaginatedLearningSections> => {
  return apiClient<PaginatedLearningSections>(
    API_ENDPOINTS.LEARNING.SECTIONS.LIST,
    {
      method: "GET",
      params,
    }
  );
};

// Corresponds to: GET /learning/sections/{slug}/
export const getLearningSectionDetails = async (
  slug: string
): Promise<LearningSection> => {
  return apiClient<LearningSection>(
    API_ENDPOINTS.LEARNING.SECTIONS.DETAIL(slug)
  );
};
