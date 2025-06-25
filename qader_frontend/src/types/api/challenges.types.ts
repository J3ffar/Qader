import { UnifiedQuestion } from "./study.types";
import { SimpleUser } from "./user.types";

// From GET /challenges/types/
export interface ChallengeTypeConfig {
  key: string;
  name: string;
  description: string;
  num_questions: number;
  time_limit_seconds: number | null;
  allow_hints: boolean;
}

export type ChallengeStatus =
  | "pending_invite"
  | "accepted"
  | "ongoing"
  | "completed"
  | "declined"
  | "cancelled";

// From GET /challenges/challenges/
export interface ChallengeList {
  id: number;
  challenger: SimpleUser;
  opponent: SimpleUser;
  challenge_type: string; // The 'key' from ChallengeTypeConfig
  challenge_type_display: string;
  status: ChallengeStatus;
  status_display: string;
  winner: SimpleUser | null;
  created_at: string; // ISO datetime string
  completed_at: string | null;
  user_is_participant: boolean;
  user_is_winner: boolean | null;
  user_score: number | null;
  opponent_score: number | null;
}

// From POST /challenges/challenges/
export interface CreateChallengePayload {
  opponent_username: string;
  challenge_type: string; // The 'key' from ChallengeTypeConfig
}

export interface ChallengeAttempt {
  id: number;
  user: SimpleUser;
  score: number;
  is_ready: boolean;
  start_time: string | null;
  end_time: string | null;
}

// From GET /challenges/challenges/{id}/
export interface ChallengeDetail
  extends Omit<
    ChallengeList,
    "user_is_participant" | "user_is_winner" | "user_score" | "opponent_score"
  > {
  attempts: ChallengeAttempt[];
  challenge_config: Record<string, any>; // Can be typed more strictly
  questions: UnifiedQuestion[]; // Populated when the challenge starts/completes
  accepted_at: string | null;
  started_at: string | null;
}

// From POST /challenges/challenges/{id}/answer/
export interface ChallengeAnswerPayload {
  question_id: number;
  selected_answer: string; // "A", "B", "C", or "D"
  time_taken_seconds: number;
}

export interface ChallengeAnswerResponse {
  status: "answer_received";
  is_correct: boolean;
  challenge_ended: boolean;
  detail: string;
  final_results?: ChallengeDetail; // Only if challenge_ended is true
}
