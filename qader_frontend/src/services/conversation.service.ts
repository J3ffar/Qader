import { API_ENDPOINTS } from "@/constants/api";
import {
  AIConfirmUnderstandingResponse,
  AIQuestionResponse,
  ConversationMessage,
  ConversationSessionDetail,
  ConversationTestResult,
  SendMessagePayload,
  StartConversationPayload,
  SubmitConversationTestAnswerPayload,
} from "@/types/api/conversation.types";
import { apiClient } from "./apiClient";

export const startConversation = (
  payload: StartConversationPayload
): Promise<ConversationSessionDetail> => {
  return apiClient<ConversationSessionDetail>(
    `${API_ENDPOINTS.STUDY.CONVERSATIONS.BASE}`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const sendMessage = (
  sessionId: number,
  payload: SendMessagePayload
): Promise<ConversationMessage> => {
  return apiClient<ConversationMessage>(
    `${API_ENDPOINTS.STUDY.CONVERSATIONS.MESSAGES(sessionId)}`,
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
    `${API_ENDPOINTS.STUDY.CONVERSATIONS.ASK_QUESTION(sessionId)}`,
    { method: "POST" }
  );
};

// UPDATED: Now returns a new response type or can be empty on 204
export const confirmUnderstanding = (
  sessionId: number
): Promise<AIConfirmUnderstandingResponse | ""> => {
  // <-- CHANGED
  return apiClient<AIConfirmUnderstandingResponse | "">(
    `${API_ENDPOINTS.STUDY.CONVERSATIONS.CONFIRM_UNDERSTANDING(sessionId)}`,
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
    `${API_ENDPOINTS.STUDY.CONVERSATIONS.SUBMIT_TEST_ANSWER(sessionId)}`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};
