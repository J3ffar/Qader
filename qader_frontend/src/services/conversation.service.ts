// src/services/conversation.service.ts
import { API_ENDPOINTS } from "@/constants/api";
import {
  AIConfirmUnderstandingResponse, // <-- NEW
  AIQuestionResponse,
  ConversationMessage,
  ConversationSessionDetail,
  ConversationTestResult,
  SendMessagePayload,
  StartConversationPayload,
  SubmitConversationTestAnswerPayload,
} from "@/types/api/conversation.types";
import { apiClient } from "./apiClient";

const CONVO_BASE = API_ENDPOINTS.STUDY.CONVERSATIONS;

export const startConversation = (
  payload: StartConversationPayload
): Promise<ConversationSessionDetail> => {
  return apiClient<ConversationSessionDetail>(`${CONVO_BASE}/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const sendMessage = (
  sessionId: number,
  payload: SendMessagePayload
): Promise<ConversationMessage> => {
  return apiClient<ConversationMessage>(
    `${CONVO_BASE}/${sessionId}/messages/`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const askForQuestion = (
  sessionId: number
): Promise<AIQuestionResponse> => {
  return apiClient<AIQuestionResponse>(
    `${CONVO_BASE}/${sessionId}/ask-question/`,
    { method: "POST" }
  );
};

// UPDATED: Now returns a new response type or can be empty on 204
export const confirmUnderstanding = (
  sessionId: number
): Promise<AIConfirmUnderstandingResponse | ""> => {
  // <-- CHANGED
  return apiClient<AIConfirmUnderstandingResponse | "">(
    `${CONVO_BASE}/${sessionId}/confirm-understanding/`,
    { method: "POST" }
  );
};

// UPDATED: Returns the new test result structure
export const submitConversationTestAnswer = (
  sessionId: number,
  payload: SubmitConversationTestAnswerPayload
): Promise<ConversationTestResult> => {
  // <-- CHANGED
  return apiClient<ConversationTestResult>(
    `${CONVO_BASE}/${sessionId}/submit-test-answer/`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};
