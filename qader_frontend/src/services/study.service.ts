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
  TraditionalPracticeStartResponse,
  HintResponse,
  RevealCorrectAnswerResponse,
  RevealExplanationResponse,
  StartTraditionalPracticePayload,
  StatisticsParams,
  UserStatistics,
  StartPracticeSimulationPayload,
  StartEmergencyModePayload,
  EmergencyModeSession,
  UpdateEmergencySessionPayload,
  UnifiedQuestion,
  SubmitEmergencyAnswerPayload,
  EmergencyModeAnswerResponse,
  StartEmergencyModeResponse,
} from "@/types/api/study.types";
import { API_ENDPOINTS } from "@/constants/api";

export const getTestAttempts = async (params?: {
  attempt_type?: string;
  attempt_type__in?: string;
  ordering?: string;
  page?: number;
  status?: string;
}): Promise<PaginatedUserTestAttempts> => {
  return apiClient<PaginatedUserTestAttempts>(
    API_ENDPOINTS.STUDY.ATTEMPTS.LIST,
    {
      method: "GET",
      params,
    }
  );
};

export const getTestAttemptDetails = async (
  attemptId: number | string
): Promise<UserTestAttemptDetail> => {
  return apiClient<UserTestAttemptDetail>(
    API_ENDPOINTS.STUDY.ATTEMPTS.DETAIL(attemptId)
  );
};

export const startLevelAssessmentTest = async (
  payload: StartLevelAssessmentPayload
): Promise<UserTestAttemptStartResponse> => {
  return apiClient<UserTestAttemptStartResponse>(
    API_ENDPOINTS.STUDY.START.LEVEL_ASSESSMENT,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const submitAnswer = async (
  attemptId: number | string,
  payload: SubmitAnswerPayload
): Promise<SubmitAnswerResponse> => {
  return apiClient<SubmitAnswerResponse>(
    API_ENDPOINTS.STUDY.ATTEMPTS.ANSWER(attemptId),
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const cancelTestAttempt = async (
  attemptId: number | string
): Promise<void> => {
  return apiClient<void>(API_ENDPOINTS.STUDY.ATTEMPTS.CANCEL(attemptId), {
    method: "POST",
  });
};

export const completeTestAttempt = async (
  attemptId: number | string
): Promise<UserTestAttemptCompletionResponse> => {
  return apiClient<UserTestAttemptCompletionResponse>(
    API_ENDPOINTS.STUDY.ATTEMPTS.COMPLETE(attemptId),
    {
      method: "POST",
    }
  );
};

export const getTestAttemptReview = async (
  attemptId: number | string,
  params?: { incorrect_only?: "true" | "false" }
): Promise<UserTestAttemptReviewResponse> => {
  return apiClient<UserTestAttemptReviewResponse>(
    API_ENDPOINTS.STUDY.ATTEMPTS.REVIEW(attemptId),
    {
      method: "GET",
      params,
    }
  );
};

export const retakeTestAttempt = async (
  attemptId: number | string
): Promise<UserTestAttemptStartResponse> => {
  return apiClient<UserTestAttemptStartResponse>(
    API_ENDPOINTS.STUDY.ATTEMPTS.RETAKE(attemptId),
    {
      method: "POST",
    }
  );
};

export const startTraditionalPractice = async (
  payload: StartTraditionalPracticePayload
): Promise<TraditionalPracticeStartResponse> => {
  return apiClient<TraditionalPracticeStartResponse>(
    API_ENDPOINTS.STUDY.START.TRADITIONAL,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const startPracticeSimulationTest = async (
  payload: StartPracticeSimulationPayload
): Promise<UserTestAttemptStartResponse> => {
  return apiClient<UserTestAttemptStartResponse>(
    API_ENDPOINTS.STUDY.START.PRACTICE_SIMULATION,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const getHintForQuestion = async (
  attemptId: string,
  questionId: number
): Promise<HintResponse> => {
  return apiClient<HintResponse>(
    API_ENDPOINTS.STUDY.TRADITIONAL_PRACTICE_INTERACTIONS.HINT(
      attemptId,
      questionId
    ),
    {
      method: "POST",
    }
  );
};

export const revealCorrectAnswerForQuestion = async (
  attemptId: string,
  questionId: number
): Promise<RevealCorrectAnswerResponse> => {
  return apiClient<RevealCorrectAnswerResponse>(
    API_ENDPOINTS.STUDY.TRADITIONAL_PRACTICE_INTERACTIONS.REVEAL_ANSWER(
      attemptId,
      questionId
    ),
    {
      method: "POST",
    }
  );
};

export const revealExplanationForQuestion = async (
  attemptId: string,
  questionId: number
): Promise<RevealExplanationResponse> => {
  return apiClient<RevealExplanationResponse>(
    API_ENDPOINTS.STUDY.TRADITIONAL_PRACTICE_INTERACTIONS.REVEAL_EXPLANATION(
      attemptId,
      questionId
    ),
    {
      method: "POST",
    }
  );
};

export const recordEliminationForQuestion = async (
  attemptId: string,
  questionId: number
): Promise<{ detail: string }> => {
  return apiClient<{ detail: string }>(
    API_ENDPOINTS.STUDY.TRADITIONAL_PRACTICE_INTERACTIONS.ELIMINATE(
      attemptId,
      questionId
    ),
    {
      method: "POST",
    }
  );
};

export const getUserStatistics = (
  params?: StatisticsParams
): Promise<UserStatistics> => {
  // FIX: Pass params object directly. apiClient handles it.
  return apiClient<UserStatistics>(API_ENDPOINTS.STUDY.STATISTICS, { params });
};

// ... Emergency Mode functions
export const startEmergencyMode = (
  payload: StartEmergencyModePayload
): Promise<StartEmergencyModeResponse> => {
  return apiClient<StartEmergencyModeResponse>(
    API_ENDPOINTS.STUDY.EMERGENCY_MODE.START,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const updateEmergencySession = ({
  sessionId,
  payload,
}: {
  sessionId: number;
  payload: UpdateEmergencySessionPayload;
}): Promise<EmergencyModeSession> => {
  return apiClient<EmergencyModeSession>(
    API_ENDPOINTS.STUDY.EMERGENCY_MODE.SESSION(sessionId),
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
};

export const getEmergencyQuestions = (
  sessionId: number
): Promise<UnifiedQuestion[]> => {
  return apiClient<UnifiedQuestion[]>(
    API_ENDPOINTS.STUDY.EMERGENCY_MODE.QUESTIONS(sessionId)
  );
};

export const submitEmergencyAnswer = ({
  sessionId,
  payload,
}: {
  sessionId: number;
  payload: SubmitEmergencyAnswerPayload;
}): Promise<EmergencyModeAnswerResponse> => {
  return apiClient<EmergencyModeAnswerResponse>(
    API_ENDPOINTS.STUDY.EMERGENCY_MODE.ANSWER(sessionId),
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};
