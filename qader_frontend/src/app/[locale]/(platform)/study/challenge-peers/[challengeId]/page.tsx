"use client"; // This page is now a client component to easily use params

import { ChallengeRoom } from "@/components/features/platform/study/challenges/ChallengeRoom";
import { useParams } from "next/navigation";

export default function ActiveChallengePage() {
  const params = useParams();
  const challengeId = params.challengeId as string;

  if (!challengeId) return null; // Or return a not found component

  // Pass the ID to the client component that will handle all real-time logic.
  return <ChallengeRoom challengeId={challengeId} />;
}
