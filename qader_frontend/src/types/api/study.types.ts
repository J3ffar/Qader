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
export type QuestionOptionKey = "A" | "B" | "C" | "D";
export type QuestionChoicesMap = {
  [key in QuestionOptionKey]: string;
};
/**
 * Represents a question's structure.
 * API: Part of UserTestAttemptStartResponse, UserTestAttemptDetail, UserTestAttemptReviewQuestion
 */
export interface QuestionSchema {
  id: number; // question_id
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  // The following are typically available during/after an attempt or review
  correct_answer?: keyof QuestionOptionKey; // "A", "B", "C", "D"
  explanation?: string | null;
  subsection_name?: string | null;
  skill_name?: string | null;
  difficulty?: number;
  hint?: string | null;
  is_starred?: boolean;
  solution_method_summary?: string | null;
  subsection?: string; // Slug or name
  skill?: string; // Slug or name
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
    selected_answer: keyof QuestionOptionKey | null;
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
  selected_answer: keyof QuestionOptionKey; // "A", "B", "C", "D"
  time_taken_seconds?: number | null;
}

/**
 * Response after submitting an answer.
 * API: POST /study/attempts/{attempt_id}/answer/
 */
export interface SubmitAnswerResponse {
  question_id: number;
  is_correct: boolean;
  correct_answer?: keyof QuestionOptionKey | null; // Revealed in some modes (e.g., Traditional)
  explanation?: string | null; // Revealed in some modes (e.g., Traditional)
  feedback_message: string; // General feedback like "Answer recorded"
}

export interface UserTestAttemptReviewScore {
  overall: number | null;
  verbal: number | null;
  quantitative: number | null;
}

export interface ResultsSummaryItem {
  correct: number;
  total: number;
  name: string; // e.g., "استيعاب المقروء"
  score: number; // Percentage for this specific sub-skill, e.g., 0 for 0%
}

export interface BadgeWon {
  slug: string;
  name: string;
  description: string;
  // Consider adding icon_url if your backend can provide it for badges
  // icon_url?: string;
}

export interface StreakInfo {
  updated: boolean;
  current_days: number;
}

/**
 * Full review details for a completed test attempt.
 * API: GET /study/attempts/{attempt_id}/review/
 * This type is enhanced to include fields typically available after test completion,
 * assuming the review endpoint can provide this rich summary.
 */
export interface UserTestAttemptReview {
  attempt_id: number;
  status?: string; // e.g., "completed", from completion data

  score: UserTestAttemptReviewScore; // Nested score object, preferred

  // For backward compatibility or if API sends both nested and flat scores:
  score_percentage: number | null; // Overall score as percentage
  score_verbal: number | null; // Verbal score as percentage
  score_quantitative: number | null; // Quantitative score as percentage

  // Detailed breakdown by sub-skill/category
  results_summary: Record<string, ResultsSummaryItem> | null;

  answered_question_count?: number;
  total_questions_api?: number; // Renamed to avoid conflict with questions.length
  correct_answers_in_test_count?: number;

  smart_analysis: string | null;
  points_from_test_completion_event?: number;
  points_from_correct_answers_this_test?: number;
  badges_won?: BadgeWon[];
  streak_info?: StreakInfo;

  // Questions for detailed review page
  questions: UserTestAttemptReviewQuestion[];

  time_taken_minutes?: number; // If available from review endpoint
  // current_level_display is handled by getQualitativeLevelInfo
}

// Ensure TestAttemptCompletionResponse is also defined if it's used elsewhere,
// (it was already provided in the prompt for context)
export interface TestAttemptCompletionResponse {
  attempt_id: number;
  status: string;
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
  streak_info: StreakInfo;
}

/**
 * Structure for a question during review.
 * API: Part of UserTestAttemptReview (GET /study/attempts/{attempt_id}/review/)
 */
export interface UserTestAttemptReviewQuestion {
  question_id: number;
  question_text: string;
  options: QuestionChoicesMap; // Changed from 'choices' to 'options'
  user_selected_choice: QuestionOptionKey | null; // Changed from 'user_answer'
  correct_answer_choice: QuestionOptionKey; // Changed from 'correct_answer'
  user_is_correct: boolean | null;
  explanation?: string | null;
  subsection_name?: string | null;
  skill_name?: string | null;
  used_hint?: boolean | null;
  used_elimination?: boolean | null;
  revealed_answer?: boolean | null;
  revealed_explanation?: boolean | null;
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
  selectedOption: keyof QuestionOptionKey | null; // A, B, C, D
  isConfirmed?: boolean; // If using a two-step confirm like the old UI
}
