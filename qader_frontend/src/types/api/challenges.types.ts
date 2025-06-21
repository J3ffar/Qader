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

// For GET /challenges/challenges/{id}/
export interface ChallengeDetail extends ChallengeList {
  // Add more detailed fields if the API provides them
  questions?: any[]; // Define a proper Question type later
}
