import { apiClient } from "./apiClient";
import { API_ENDPOINTS } from "../constants/api";
import { PaginatedResponse } from "../types/api";
import {
  ChallengeList,
  CreateChallengePayload,
} from "../types/api/challenges.types";

export const getChallenges = async (filters: Record<string, any> = {}) => {
  const response = await apiClient<PaginatedResponse<ChallengeList>>(
    API_ENDPOINTS.STUDY.CHALLENGES.LIST_AND_CREATE,
    { params: filters }
  );
  return response;
};

export const createChallenge = async (payload: CreateChallengePayload) => {
  const response = await apiClient<ChallengeList>(
    API_ENDPOINTS.STUDY.CHALLENGES.LIST_AND_CREATE,
    { method: "POST", body: JSON.stringify(payload) }
  );
  return response;
};

export const acceptChallenge = async (id: number | string) => {
  const response = await apiClient<ChallengeList>(
    API_ENDPOINTS.STUDY.CHALLENGES.ACCEPT(id),
    { method: "POST" }
  );
  return response;
};

// ... create similar functions for declineChallenge, cancelChallenge, rematchChallenge
