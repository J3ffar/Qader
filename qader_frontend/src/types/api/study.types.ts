import { PaginatedResponse } from ".";

// =================================================================
// PRIMARY SHARED OBJECTS (as per new API spec)
// =================================================================

/**
 * The standard and only structure to represent a question.
 * Replaces all previous fragmented question types.
 * API: /learning/questions/, test start, test detail, test review
 */
export interface UnifiedQuestion {
  id: number;
  question_text: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  difficulty: number;
  hint: string | null;
  solution_method_summary: string | null;
  correct_answer: "A" | "B" | "C" | "D";
  explanation: string | null;
  section: {
    id: number;
    name: string;
    slug: string;
  };
  subsection: {
    id: number;
    name: string;
    slug: string;
    description: string | null;
    order: number;
    is_active: boolean;
  };
  skill: {
    id: number;
    name: string;
    slug: string;
    description: string | null;
  } | null;
  is_starred: boolean;
  // This field is ONLY populated in the context of a specific test review.
  user_answer_details: {
    selected_choice: "A" | "B" | "C" | "D" | null;
    is_correct: boolean | null;
    used_hint?: boolean | null;
    used_elimination?: boolean | null;
    revealed_answer?: boolean | null;
    revealed_explanation?: boolean | null;
  } | null;
}

// =================================================================
// TEST ATTEMPT LIFECYCLE (as per new API spec)
// =================================================================

/**
 * Brief summary for a list of test attempts.
 * API: GET /study/attempts/
 */
export interface UserTestAttemptList {
  attempt_id: number;
  test_type: string;
  date: string; // ISO datetime string
  status: "started" | "completed" | "abandoned";
  status_display: string;
  num_questions: number;
  answered_question_count: number;
  score_percentage: number | null;
  performance: {
    overall: number | null;
    verbal: number | null;
    quantitative: number | null;
  } | null;
}

export type PaginatedUserTestAttempts = PaginatedResponse<UserTestAttemptList>;

/**
 * Full details for an ongoing or completed test attempt.
 * API: GET /study/attempts/{attempt_id}/
 */
export interface UserTestAttemptDetail
  extends Omit<UserTestAttemptList, "performance"> {
  config_name: string | null;
  start_time: string;
  end_time: string | null;
  score_verbal: number | null;
  score_quantitative: number | null;
  included_questions: UnifiedQuestion[];
  attempted_questions: Array<{
    question_id: number;
    question_text_preview: string;
    selected_answer: "A" | "B" | "C" | "D" | null;
    is_correct: boolean | null;
    attempted_at: string;
  }>;
  results_summary: Record<string, ResultsSummaryItem> | null;
  configuration_snapshot: Record<string, any> | null;
}

/**
 * Response when starting any new test.
 * API: POST /study/start/..., POST /study/attempts/{attempt_id}/retake/
 */
export interface UserTestAttemptStartResponse {
  attempt_id: number;
  attempt_number_for_type: number;
  questions: UnifiedQuestion[];
}

/**
 * ACCURATE TYPE: Response from POST /study/attempts/{id}/complete/
 * This contains the full one-time result including gamification.
 * It is the primary data source for the Score Page.
 */
export interface UserTestAttemptCompletionResponse {
  attempt_id: number;
  status: string; // e.g., "completed"
  score: {
    overall: number | null;
    verbal: number | null;
    quantitative: number | null;
  };
  results_summary: Record<string, ResultsSummaryItem> | null;
  answered_question_count: number;
  total_questions: number;
  correct_answers_in_test_count: number;
  smart_analysis: string | null;
  points_from_test_completion_event: number;
  points_from_correct_answers_this_test: number;
  badges_won: BadgeWon[];
  streak_info: StreakInfo | null;
}

/**
 * ACCURATE TYPE: Response from GET /study/attempts/{id}/review/
 * This contains data for a detailed question-by-question review.
 * It is the data source for the Review Page and a fallback for the Score Page.
 */
export interface UserTestAttemptReviewResponse {
  attempt_id: number;
  questions: UnifiedQuestion[]; // Each with populated `user_answer_details`
  score_percentage: number | null; // Note: This is the overall score for this endpoint
  score_verbal: number | null;
  score_quantitative: number | null;
  results_summary: Record<string, ResultsSummaryItem> | null;
  // Let's also add the total question count from the completion response for consistency if available,
  // otherwise we can calculate it from questions.length
  total_questions?: number;
  answered_question_count?: number;
  correct_answers_in_test_count?: number;
  time_taken_minutes?: number | null; // Assuming this might come from another source or be added later
}

// =================================================================
// PAYLOADS & OTHER HELPER TYPES
// =================================================================

export interface BadgeWon {
  slug: string;
  name: string;
  description: string;
}

export interface StreakInfo {
  updated: boolean;
  current_days: number;
}

export interface ResultsSummaryItem {
  correct: number;
  total: number;
  name: string;
  score: number;
}

export interface SubmitAnswerPayload {
  question_id: number;
  selected_answer: "A" | "B" | "C" | "D";
  time_taken_seconds?: number | null;
}

export interface SubmitAnswerResponse {
  question: UnifiedQuestion; // The full question object, updated with user_answer_details
  feedback_message: string;
}

export interface StartLevelAssessmentPayload {
  sections: string[]; // e.g., ["verbal", "quantitative"]
  num_questions: number;
}

export interface StartTraditionalPracticePayload {
  subsections?: string[];
  skills?: string[];
  num_questions?: number;
  starred?: boolean;
  not_mastered?: boolean;
}

export interface TraditionalPracticeStartResponse {
  attempt_id: number;
  status: "started";
  attempt_number_for_type: number;
  questions: UnifiedQuestion[];
}

export interface HintResponse {
  question_id: number;
  hint: string | null;
}

export interface RevealCorrectAnswerResponse {
  question_id: number;
  correct_answer: "A" | "B" | "C" | "D";
}

export interface RevealExplanationResponse {
  question_id: number;
  explanation: string | null;
}
