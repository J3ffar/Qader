"use client";

import { ChallengeCard } from "./ChallengeCard";
import { ChallengeList } from "@/types/api/challenges.types";

interface ChallengesListProps {
  challenges: ChallengeList[];
  emptyMessage: string;
}

export function ChallengesList({
  challenges,
  emptyMessage,
}: ChallengesListProps) {
  if (challenges.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-8">{emptyMessage}</p>
    );
  }

  return (
    <div className="grid gap-4">
      {challenges.map((challenge) => (
        <ChallengeCard key={challenge.id} challenge={challenge} />
      ))}
    </div>
  );
}
