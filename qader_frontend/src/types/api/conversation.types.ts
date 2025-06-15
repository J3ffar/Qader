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
  current_topic_question_id: number | null;
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

export interface SubmitConversationTestAnswerPayload {
  question_id: number;
  selected_answer: "A" | "B" | "C" | "D";
}

export interface ConversationTestResult {
  question: UnifiedQuestion; // Full question with correct answer and explanation
  user_answer_details: {
    selected_choice: "A" | "B" | "C" | "D" | null;
    is_correct: boolean | null;
  };
  ai_feedback: string;
}

// Custom type for the UI state, combining different message possibilities
export type CustomMessageType =
  | { type: "text"; content: ConversationMessage }
  | { type: "question"; content: AIQuestionResponse; sender: "ai" }
  | { type: "feedback"; content: ConversationTestResult; sender: "ai" };
