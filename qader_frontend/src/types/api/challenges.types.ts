import { UnifiedQuestion } from "./study.types";
import { SimpleUser } from "./user.types";

export type ChallengeStatus =
  | "pending_invite"
  | "pending_matchmaking"
  | "accepted"
  | "ongoing"
  | "completed"
  | "declined"
  | "cancelled"
  | "expired";

export type ChallengeType =
  | "quick_quant_10"
  | "medium_verbal_15"
  | "comprehensive_20"
  | "speed_challenge_5min"
  | "accuracy_challenge"
  | "custom";

// For GET /challenges/challenges/
export interface ChallengeList {
  id: number;
  challenger: SimpleUser;
  opponent: SimpleUser;
  challenge_type: ChallengeType;
  challenge_type_display: string;
  status: ChallengeStatus;
  status_display: string;
  winner: SimpleUser | null;
  created_at: string; // ISO datetime string
  completed_at: string | null;
  user_is_participant: boolean | null;
  user_is_winner: boolean | null;
  user_score: number | null;
  opponent_score: number | null;
}

// For POST /challenges/challenges/
export interface CreateChallengePayload {
  opponent_username?: string | null;
  challenge_type: ChallengeType;
}

interface ChallengeAttempt {
  id: number;
  user: SimpleUser;
  score: number;
  is_ready: boolean;
  start_time: string | null;
  end_time: string | null;
}

// For GET /challenges/challenges/{id}/
export interface ChallengeDetail extends ChallengeList {
  attempts: ChallengeAttempt[];
  challenge_config: any; // Can be typed more strictly if config structure is known
  questions: UnifiedQuestion[]; // Use a proper question type
  accepted_at: string | null;
  started_at: string | null;
}

export interface ChallengeAnswerPayload {
  question_id: number;
  selected_answer: string; // "A", "B", "C", or "D"
}

// Type for the response after submitting an answer
// Based on the WebSocket docs, this is what the backend might return.
export interface ChallengeAnswerResponse {
  user_id: number;
  question_id: number;
  is_correct: boolean;
  selected_answer: string;
  current_score: number;
}
