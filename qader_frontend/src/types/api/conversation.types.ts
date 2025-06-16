import { UnifiedQuestion } from "./study.types";

export type AITone = "cheerful" | "serious";

export interface ConversationMessage {
  id: number;
  sender_type: "user" | "ai";
  message_text: string;
  related_question_id: number | null;
  timestamp: string; // ISO datetime string
}

export interface ConversationSessionDetail {
  id: number;
  url: string;
  user: {
    id: number;
    full_name: string;
  };
  ai_tone: AITone;
  status: "active" | "completed";
  start_time: string;
  end_time: string | null;
  updated_at: string;
  messages: ConversationMessage[];
  current_topic_question: UnifiedQuestion | null; // <-- CHANGED
}

export interface StartConversationPayload {
  ai_tone?: AITone;
}

export interface SendMessagePayload {
  message_text: string;
  related_question_id?: number | null;
}

export interface AIQuestionResponse {
  ai_message: string;
  question: UnifiedQuestion;
}

// NEW: Type for the `confirm-understanding` endpoint response
export interface AIConfirmUnderstandingResponse {
  ai_message: string;
  test_question: UnifiedQuestion;
}

export interface SubmitConversationTestAnswerPayload {
  question_id: number;
  selected_answer: "A" | "B" | "C" | "D";
}

// UPDATED: Completely new flat structure for the test result
export interface ConversationTestResult {
  id: number;
  question: UnifiedQuestion; // Includes correct_answer and explanation
  selected_answer: "A" | "B" | "C" | "D";
  is_correct: boolean;
  attempted_at: string; // ISO datetime string
  ai_feedback: string;
}

// Custom type for the UI state, combining different message possibilities
export type CustomMessageType =
  | { type: "text"; content: ConversationMessage }
  | { type: "question"; content: AIQuestionResponse; sender: "ai" }
  | { type: "feedback"; content: ConversationTestResult; sender: "ai" };
