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

// Corresponds to: POST /learning/questions/{id}/star/
export const starQuestion = async (
  questionId: number
): Promise<{ status: string }> => {
  return apiClient<{ status: string }>(
    API_ENDPOINTS.LEARNING.QUESTIONS.STAR(questionId),
    {
      method: "POST",
    }
  );
};

// Corresponds to: DELETE /learning/questions/{id}/star/
export const unstarQuestion = async (questionId: number): Promise<void> => {
  return apiClient(API_ENDPOINTS.LEARNING.QUESTIONS.UNSTAR(questionId), {
    method: "DELETE",
  });
};
