// src/services/study.service.ts
import { apiClient } from "./apiClient";
import {
  PaginatedUserTestAttempts,
  UserTestAttemptDetail,
  UserTestAttemptStartResponse,
  StartLevelAssessmentPayload,
  SubmitAnswerPayload,
  SubmitAnswerResponse,
  UserTestAttemptCompletionResponse,
  UserTestAttemptReviewResponse,
} from "@/types/api/study.types";
import { API_ENDPOINTS } from "@/constants/api"; // Assuming this exists and has study endpoints

const STUDY_API_BASE = "/study"; // Or define more specific paths in API_ENDPOINTS

// Corresponds to: GET /study/attempts/
export const getTestAttempts = async (params?: {
  attempt_type?: string;
  ordering?: string;
  page?: number;
  status?: string;
}): Promise<PaginatedUserTestAttempts> => {
  return apiClient<PaginatedUserTestAttempts>(`${STUDY_API_BASE}/attempts/`, {
    method: "GET",
    params, // apiClient needs to handle params correctly for GET
  });
};

// Corresponds to: GET /study/attempts/{attempt_id}/
export const getTestAttemptDetails = async (
  attemptId: number | string
): Promise<UserTestAttemptDetail> => {
  return apiClient<UserTestAttemptDetail>(
    `${STUDY_API_BASE}/attempts/${attemptId}/`
  );
};

// Corresponds to: POST /study/start/level-assessment/
export const startLevelAssessmentTest = async (
  payload: StartLevelAssessmentPayload
): Promise<UserTestAttemptStartResponse> => {
  return apiClient<UserTestAttemptStartResponse>(
    `${STUDY_API_BASE}/start/level-assessment/`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

// Corresponds to: POST /study/attempts/{attempt_id}/answer/
export const submitAnswer = async (
  attemptId: number | string,
  payload: SubmitAnswerPayload
): Promise<SubmitAnswerResponse> => {
  return apiClient<SubmitAnswerResponse>(
    `${STUDY_API_BASE}/attempts/${attemptId}/answer/`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

// Corresponds to: POST /study/attempts/{attempt_id}/cancel/
export const cancelTestAttempt = async (
  attemptId: number | string
): Promise<void> => {
  // Assuming 204 No Content or simple success message
  return apiClient<void>(`${STUDY_API_BASE}/attempts/${attemptId}/cancel/`, {
    method: "POST",
  });
};

// Corresponds to: POST /study/attempts/{attempt_id}/complete/
export const completeTestAttempt = async (
  attemptId: number | string
): Promise<UserTestAttemptCompletionResponse> => {
  // Correct return type
  return apiClient<UserTestAttemptCompletionResponse>(
    `${STUDY_API_BASE}/attempts/${attemptId}/complete/`,
    {
      method: "POST",
    }
  );
};

// Corresponds to: GET /study/attempts/{attempt_id}/review/
export const getTestAttemptReview = async (
  attemptId: number | string,
  params?: { incorrect_only?: "true" | "false" }
): Promise<UserTestAttemptReviewResponse> => {
  // Correct return type
  return apiClient<UserTestAttemptReviewResponse>(
    `${STUDY_API_BASE}/attempts/${attemptId}/review/`,
    {
      method: "GET",
      params,
    }
  );
};

// Corresponds to: POST /study/attempts/{attempt_id}/retake/
export const retakeTestAttempt = async (
  attemptId: number | string
): Promise<UserTestAttemptStartResponse> => {
  return apiClient<UserTestAttemptStartResponse>(
    `${STUDY_API_BASE}/attempts/${attemptId}/retake/`,
    {
      method: "POST",
    }
  );
};
