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

/**
 * Payload for starting a Practice or Simulation Test.
 * API: POST /study/start/practice-simulation/
 */
export interface StartPracticeSimulationPayload {
  test_type: "practice" | "simulation";
  config: {
    name?: string | null;
    subsections?: string[];
    skills?: string[];
    num_questions: number;
    starred?: boolean;
    not_mastered?: boolean;
  };
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

// Params for the statistics API call
export interface StatisticsParams {
  [key: string]: string | undefined; // This is the fix. It adds the index signature.
  aggregation_period?: "daily" | "weekly" | "monthly" | "yearly";
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
}

// Full response structure for GET /study/statistics/
export interface UserStatistics {
  overall: {
    mastery_level: {
      verbal: number | null;
      quantitative: number | null;
    };
    study_streaks: {
      current_days: number;
      longest_days: number;
    };
    activity_summary: {
      total_questions_answered: number;
      total_tests_completed: number;
    };
  };
  performance_by_section: {
    [section_slug: string]: {
      name: string;
      overall_accuracy: number | null;
      subsections: {
        [subsection_slug: string]: {
          name: string;
          accuracy: number | null;
          attempts: number;
        };
      };
    };
  };
  skill_proficiency_summary: Array<{
    skill_slug: string;
    skill_name: string;
    proficiency_score: number;
    accuracy: number | null;
    attempts: number;
  }>;
  test_history_summary: Array<{
    attempt_id: number;
    date: string;
    type: string;
    type_value: string;
    overall_score: number | null;
    verbal_score: number | null;
    quantitative_score: number | null;
    num_questions: number;
  }>;
  performance_trends_by_test_type: {
    [test_type_value: string]: Array<{
      // Structure for aggregated data
      period_start_date?: string;
      average_score?: number | null;
      average_verbal_score?: number | null;
      average_quantitative_score?: number | null;
      test_count?: number;
      // Structure for non-aggregated data
      attempt_id?: number;
      date?: string;
      score?: number | null;
      verbal_score?: number | null;
      quantitative_score?: number | null;
      num_questions?: number;
    }>;
  };
  average_scores_by_test_type: {
    [test_type_value: string]: {
      attempt_type_value: string;
      attempt_type_display: string;
      average_score: number | null;
      average_verbal_score: number | null;
      average_quantitative_score: number | null;
      test_count: number;
    };
  };
  time_analytics: {
    overall_average_time_per_question_seconds: number | null;
    average_time_per_question_by_correctness: {
      correct: {
        average_time_seconds: number | null;
        question_count: number;
      };
      incorrect: {
        average_time_seconds: number | null;
        question_count: number;
      };
    };
    average_test_duration_by_type: {
      [test_type_value: string]: {
        attempt_type_value: string;
        attempt_type_display: string;
        average_duration_seconds: number | null;
        test_count: number;
      };
    };
  };
}

// =================================================================
// EMERGENCY MODE
// =================================================================

/**
 * Payload for starting an Emergency Mode session.
 * API: POST /study/emergency/start/
 */
export interface StartEmergencyModePayload {
  days_until_test: number;
  reason?: string;
  available_time_hours?: number;
  focus_areas?: Array<"verbal" | "quantitative">;
}

/**
 * A skill targeted in the emergency plan.
 */
export interface TargetSkill {
  slug: string;
  name: string;
  reason: string;
  current_proficiency: number;
  subsection_name: string;
}

/**
 * UPDATED: A topic for quick review in the emergency plan.
 */
export interface QuickReviewTopic {
  slug: string;
  name: string;
  description: string;
  reason: string;
  current_proficiency: number;
}

/**
 * The detailed study plan returned when starting a session.
 */
export interface SuggestedPlan {
  focus_area_names: string[];
  estimated_duration_minutes: number;
  recommended_question_count: number;
  target_skills: TargetSkill[];
  quick_review_topics: QuickReviewTopic[];
  motivational_tips: string[];
}

/**
 * Response from starting an Emergency Mode session.
 * API: POST /study/emergency/start/
 */
export interface StartEmergencyModeResponse {
  session_id: number;
  suggested_plan: SuggestedPlan;
}

/**
 * The full session object, returned when updating settings.
 * API: PATCH /study/emergency/sessions/{session_id}/
 */
export interface EmergencyModeSession {
  id: number;
  start_time: string;
  available_time_hours: number | null;
  calm_mode_active: boolean;
  shared_with_admin: boolean;
  focus_areas: Array<"verbal" | "quantitative">;
  suggested_plan: SuggestedPlan | null;
}

/**
 * Payload for updating an Emergency Mode session's settings.
 * API: PATCH /study/emergency/sessions/{session_id}/
 */
export interface UpdateEmergencySessionPayload {
  calm_mode_active?: boolean;
  shared_with_admin?: boolean;
}

/**
 * Payload for submitting an answer in Emergency Mode (body only).
 * API: POST /study/emergency/sessions/{session_id}/answer/
 */
export interface SubmitEmergencyAnswerPayload {
  question_id: number;
  selected_answer: "A" | "B" | "C" | "D";
}

/**
 * Response after submitting an answer in Emergency Mode.
 * API: POST /study/emergency/sessions/{session_id}/answer/
 */
export interface EmergencyModeAnswerResponse {
  question_id: number;
  is_correct: boolean;
  correct_answer: "A" | "B" | "C" | "D";
  explanation: string | null;
  feedback: string; // Renamed from feedback_message
}

// API: POST /study/emergency/sessions/{session_id}/complete/
export interface EmergencyModeCompleteResponse {
  session_id: number;
  overall_score: number;
  verbal_score: number | null;
  quantitative_score: number | null;
  results_summary: {
    [key: string]: {
      name: string;
      score: number;
      subsections: {
        [key: string]: {
          name: string;
          score: number;
        };
      };
    };
  };
  ai_feedback: string;
  answered_question_count: number;
  correct_answers_count: number;
}

// API: POST /study/emergency/sessions/{session_id}/request-support/
export interface RequestSupportPayload {
  problem_type: "technical" | "academic" | "content" | "other";
  description: string;
}

export interface EmergencySupportRequest {
  id: number;
  problem_type: string;
  description: string;
  status: string;
  created_at: string;
}
