import { apiClient } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import { PaginatedResponse } from "@/types/api";
import {
  ChallengeDetail,
  ChallengeList,
  CreateChallengePayload,
  ChallengeAnswerPayload,
  ChallengeAnswerResponse,
  ChallengeTypeConfig,
} from "@/types/api/challenges.types";

/**
 * Fetches a list of all available challenge types.
 */
export const getChallengeTypes = async (): Promise<ChallengeTypeConfig[]> => {
  const response = await apiClient<ChallengeTypeConfig[]>(
    API_ENDPOINTS.STUDY.CHALLENGES.TYPES
  );
  return response;
};

/**
 * Fetches a paginated list of challenges for the current user.
 * Supports filtering via query parameters.
 */
export const getChallenges = async (
  filters: { status?: string; is_pending_invite_for_user?: boolean } = {}
): Promise<PaginatedResponse<ChallengeList>> => {
  const response = await apiClient<PaginatedResponse<ChallengeList>>(
    API_ENDPOINTS.STUDY.CHALLENGES.LIST_AND_CREATE,
    { params: filters }
  );
  return response;
};

/**
 * Creates a new challenge against another user.
 */
export const createChallenge = async (
  payload: CreateChallengePayload
): Promise<ChallengeDetail> => {
  const response = await apiClient<ChallengeDetail>(
    API_ENDPOINTS.STUDY.CHALLENGES.LIST_AND_CREATE,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
  return response;
};

/**
 * Accepts a pending challenge invitation.
 */
export const acceptChallenge = async (
  id: number | string
): Promise<ChallengeDetail> => {
  const response = await apiClient<ChallengeDetail>(
    API_ENDPOINTS.STUDY.CHALLENGES.ACCEPT(id),
    { method: "POST" }
  );
  return response;
};

/**
 * Declines a pending challenge invitation.
 */
export const declineChallenge = async (
  id: number | string
): Promise<{ status: "declined"; detail: string }> => {
  const response = await apiClient<{ status: "declined"; detail: string }>(
    API_ENDPOINTS.STUDY.CHALLENGES.DECLINE(id),
    { method: "POST" }
  );
  return response;
};

/**
 * Cancels a challenge that the current user created.
 */
export const cancelChallenge = async (
  id: number | string
): Promise<{ status: "cancelled"; detail: string }> => {
  const response = await apiClient<{ status: "cancelled"; detail: string }>(
    API_ENDPOINTS.STUDY.CHALLENGES.CANCEL(id),
    { method: "POST" }
  );
  return response;
};

/**
 * Fetches the detailed state of a single challenge.
 */
export const getChallengeDetails = async (
  id: string | number
): Promise<ChallengeDetail> => {
  const response = await apiClient<ChallengeDetail>(
    API_ENDPOINTS.STUDY.CHALLENGES.DETAIL(id)
  );
  return response;
};

/**
 * Marks the current user as "ready" to start an accepted challenge.
 */
export const markAsReady = async (
  id: number | string
): Promise<{
  user_status: string;
  challenge_status: string;
  challenge_started: boolean;
  detail: string;
}> => {
  const response = await apiClient<any>(
    API_ENDPOINTS.STUDY.CHALLENGES.READY(id),
    { method: "POST" }
  );
  return response;
};

/**
 * Submits an answer for a specific question within an ongoing challenge.
 */
export const submitChallengeAnswer = async (
  id: number | string,
  payload: ChallengeAnswerPayload
): Promise<ChallengeAnswerResponse> => {
  const response = await apiClient<ChallengeAnswerResponse>(
    API_ENDPOINTS.STUDY.CHALLENGES.ANSWER(id),
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
  return response;
};

/**
 * Retrieves the final results of a completed challenge.
 */
export const getChallengeResults = async (
  id: string | number
): Promise<ChallengeDetail> => {
  const response = await apiClient<ChallengeDetail>(
    API_ENDPOINTS.STUDY.CHALLENGES.RESULTS(id)
  );
  return response;
};

/**
 * Initiates a rematch for a completed challenge.
 */
export const createRematch = async (
  id: number | string
): Promise<ChallengeDetail> => {
  const response = await apiClient<ChallengeDetail>(
    API_ENDPOINTS.STUDY.CHALLENGES.REMATCH(id),
    { method: "POST" }
  );
  return response;
};
