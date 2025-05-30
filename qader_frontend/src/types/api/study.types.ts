import { PaginatedResponse } from ".";

/**
 * Represents a brief summary of a user's test attempt, typically used in lists.
 * API: GET /study/attempts/
 */
export interface UserTestAttemptBrief {
  attempt_id: number;
  test_type:
    | "level_assessment"
    | "practice"
    | "simulation"
    | "traditional"
    | string;
  date: string; // ISO datetime string (e.g., start_time)
  status: "started" | "completed" | "abandoned" | string;
  status_display: string;
  num_questions: number;
  answered_question_count: number;
  score_percentage: number | null;
  // Performance can vary, making it flexible.
  // Example: { "verbal": 75.0, "quantitative": 80.0, "overall_calculated": 77.5 }
  // Or specific levels if API sends that for level assessment:
  // verbal?: "ممتاز" | "جيد جداً" | "ضعيف" | string; (This was in old mock, API might give numeric)
  // quantitative?: "ممتاز" | "جيد جداً" | "ضعيف" | string;
  performance: Record<string, number | string> | null;

  // Added based on provided frontend code for level assessment list
  // These might come from a transformed 'performance' object or directly if API supports it.
  // It's better if API returns numeric scores and frontend maps to qualitative terms if needed.
  verbal_level_display?: string;
  quantitative_level_display?: string;
}

export type PaginatedUserTestAttempts = PaginatedResponse<UserTestAttemptBrief>;

/**
 * Represents choices for a multiple-choice question.
 */
export interface QuestionChoices {
  A: string;
  B: string;
  C: string;
  D: string;
}

/**
 * Represents a question's structure.
 * API: Part of UserTestAttemptStartResponse, UserTestAttemptDetail, UserTestAttemptReviewQuestion
 */
export interface QuestionSchema {
  id: number; // question_id
  question_text: string;
  choices: QuestionChoices; // Assuming options come as an object A, B, C, D
  // The following are typically available during/after an attempt or review
  correct_answer?: keyof QuestionChoices; // "A", "B", "C", "D"
  explanation?: string | null;
  subsection_name?: string | null;
  skill_name?: string | null;
}

/**
 * Response when starting a new test attempt.
 * API: POST /study/start/level-assessment/, POST /study/start/practice-simulation/, POST /study/attempts/{attempt_id}/retake/
 */
export interface UserTestAttemptStartResponse {
  attempt_id: number;
  attempt_number_for_type: number;
  questions: QuestionSchema[]; // Initial set of questions
  // Potentially other details like time limit if set by backend
}

/**
 * Detailed information about a specific test attempt.
 * API: GET /study/attempts/{attempt_id}/
 */
export interface UserTestAttemptDetail extends UserTestAttemptBrief {
  config_name: string | null; // Name of the test configuration
  start_time: string; // ISO datetime
  end_time: string | null; // ISO datetime
  score_verbal: number | null;
  score_quantitative: number | null;
  included_questions: QuestionSchema[]; // All questions in this attempt
  attempted_questions: Array<{
    question_id: number;
    question_text_preview: string;
    selected_answer: keyof QuestionChoices | null;
    is_correct: boolean | null;
    attempted_at: string; // ISO datetime
  }>;
  results_summary: Record<string, any> | null; // Define more specifically if structure is known
  configuration_snapshot: Record<string, any> | null; // The configuration used for this test
}

/**
 * Payload for submitting an answer.
 * API: POST /study/attempts/{attempt_id}/answer/
 */
export interface SubmitAnswerPayload {
  question_id: number;
  selected_answer: keyof QuestionChoices; // "A", "B", "C", "D"
  time_taken_seconds?: number | null;
}

/**
 * Response after submitting an answer.
 * API: POST /study/attempts/{attempt_id}/answer/
 */
export interface SubmitAnswerResponse {
  question_id: number;
  is_correct: boolean;
  correct_answer?: keyof QuestionChoices | null; // Revealed in some modes (e.g., Traditional)
  explanation?: string | null; // Revealed in some modes (e.g., Traditional)
  feedback_message: string; // General feedback like "Answer recorded"
}

/**
 * Response after completing a test attempt.
 * API: POST /study/attempts/{attempt_id}/complete/
 */
export interface TestAttemptCompletionResponse {
  attempt_id: number;
  status: string; // e.g., "completed"
  score: {
    overall: number | null;
    verbal: number | null;
    quantitative: number | null;
  };
  results_summary: Record<string, any> | null;
  answered_question_count: number;
  total_questions: number;
  correct_answers_in_test_count: number;
  smart_analysis: string | null;
  points_from_test_completion_event: number;
  points_from_correct_answers_this_test: number;
  badges_won: Array<{
    slug: string;
    name: string;
    description: string;
  }>;
  streak_info: {
    updated: boolean;
    current_days: number;
  };
}

/**
 * Structure for a question during review.
 * API: Part of UserTestAttemptReview
 */
export interface UserTestAttemptReviewQuestion extends QuestionSchema {
  user_answer: keyof QuestionChoices | null;
  user_is_correct: boolean | null;
  // Fields specific to traditional mode or review context
  used_hint?: boolean | null;
  used_elimination?: boolean | null;
  revealed_answer?: boolean | null;
  revealed_explanation?: boolean | null;
}

/**
 * Full review details for a completed test attempt.
 * API: GET /study/attempts/{attempt_id}/review/
 */
export interface UserTestAttemptReview {
  attempt_id: number;
  questions: UserTestAttemptReviewQuestion[];
  score_percentage: number | null;
  score_verbal: number | null;
  score_quantitative: number | null;
  results_summary: Record<string, any> | null; // Detailed breakdown
  // These fields were in the old score page, API docs for review don't explicitly list them
  // but they might be part of results_summary or calculated from score_percentage
  time_taken_minutes?: number; // Example
  current_level_display?: string; // Example
  advice?: string; // Example: "ينصح بمراجعة قسم القواعد اللفظية"
}

/**
 * Payload for starting a level assessment test.
 * API: POST /study/start/level-assessment/
 */
export interface StartLevelAssessmentPayload {
  sections: string[]; // e.g., ["verbal", "quantitative"]
  num_questions: number;
}

// For the "Start Level Assessment" form using React Hook Form + Zod
export interface StartLevelAssessmentFormValues {
  sections: string[];
  num_questions: number;
}

// For the quiz page [attemptId]/page.tsx
export interface QuizUserAnswer {
  questionId: number;
  selectedOption: keyof QuestionChoices | null; // A, B, C, D
  isConfirmed?: boolean; // If using a two-step confirm like the old UI
}
