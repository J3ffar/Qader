import { apiClient } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import { PaginatedResponse } from "@/types/api";
import {
  ChallengeDetail,
  ChallengeList,
  CreateChallengePayload,
  ChallengeAnswerPayload, // Assuming this type will be created
  ChallengeAnswerResponse, // Assuming this type will be created
} from "@/types/api/challenges.types";

/**
 * Fetches a paginated list of challenges for the current user.
 * Supports filtering via query parameters.
 */
export const getChallenges = async (
  filters: Record<string, any> = {}
): Promise<PaginatedResponse<ChallengeList>> => {
  const response = await apiClient<PaginatedResponse<ChallengeList>>(
    API_ENDPOINTS.STUDY.CHALLENGES.LIST_AND_CREATE,
    { params: filters }
  );
  return response;
};

/**
 * Creates a new challenge.
 * Can be against a specific opponent or random matchmaking.
 */
export const createChallenge = async (
  payload: CreateChallengePayload
): Promise<ChallengeList> => {
  const response = await apiClient<ChallengeList>(
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
): Promise<ChallengeList> => {
  const response = await apiClient<ChallengeList>(
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
): Promise<ChallengeList> => {
  const response = await apiClient<ChallengeList>(
    API_ENDPOINTS.STUDY.CHALLENGES.DECLINE(id),
    { method: "POST" }
  );
  return response;
};

/**
 * Cancels a challenge that the current user created and is still pending.
 */
export const cancelChallenge = async (
  id: number | string
): Promise<ChallengeList> => {
  const response = await apiClient<ChallengeList>(
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
 * The backend will typically start the challenge once all participants are ready.
 */
export const markAsReady = async (
  id: number | string
): Promise<ChallengeDetail> => {
  const response = await apiClient<ChallengeDetail>(
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
 * Initiates a rematch for a completed challenge.
 * This creates a new challenge with a pending invite for the other player.
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
