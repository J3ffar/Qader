import { apiClient } from "./apiClient";
import {
  PaginatedLearningSections,
  LearningSection,
} from "@/types/api/learning.types";
// Assuming API_ENDPOINTS might have a specific path for learning, or use a base.
const LEARNING_API_BASE = "/learning";

// Corresponds to: GET /learning/sections/
export const getLearningSections = async (params?: {
  ordering?: string;
  page?: number;
}): Promise<PaginatedLearningSections> => {
  return apiClient<PaginatedLearningSections>(
    `${LEARNING_API_BASE}/sections/`,
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
  return apiClient<LearningSection>(`${LEARNING_API_BASE}/sections/${slug}/`);
};
