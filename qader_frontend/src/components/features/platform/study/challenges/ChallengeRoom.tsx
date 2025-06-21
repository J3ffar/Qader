"use client";

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { getChallengeDetails } from "@/services/challenges.service"; // Assuming this function exists
import { queryKeys } from "@/constants/queryKeys";
import { useWebSocket, ConnectionStatus } from "@/hooks/useWebSocket";
import { ChallengeDetail } from "@/types/api/challenges.types";

import { ChallengeLobby } from "./room/ChallengeLobby"; // Placeholder for pre-game UI
import { ChallengeInProgress } from "./room/ChallengeInProgress"; // Placeholder for game UI
import { ChallengeResults } from "./room/ChallengeResults"; // Placeholder for post-game UI
import { ChallengeSkeletons } from "./ChallengeSkeletons"; // Reusing skeletons
import { WS_BASE_URL } from "@/constants/api";

interface ChallengeRoomProps {
  challengeId: string;
}

export function ChallengeRoom({ challengeId }: ChallengeRoomProps) {
  const t = useTranslations("study.challenges");
  const queryClient = useQueryClient();

  const challengeQueryKey = queryKeys.challenges.detail(challengeId);

  // 1. Fetch initial data using TanStack Query
  const {
    data: challengeData,
    isLoading,
    isError,
  } = useQuery<ChallengeDetail>({
    queryKey: challengeQueryKey,
    queryFn: () => getChallengeDetails(challengeId),
    staleTime: Infinity, // Data will be kept fresh by WebSockets
  });

  // 2. Establish WebSocket connection for this specific challenge
  const wsUrl = `${WS_BASE_URL}/challenges/${challengeId}/`;
  const { lastMessage, connectionStatus } = useWebSocket(wsUrl, {
    shouldConnect: !!challengeId,
  });

  // 3. Process incoming WebSocket messages to update the TanStack Query cache
  useEffect(() => {
    if (!lastMessage) return;

    const { type, payload } = lastMessage;

    switch (type) {
      case "challenge.update":
      case "challenge.start":
      case "challenge.end":
        // These events provide the full, updated challenge object.
        // We directly update the cache with this new data.
        queryClient.setQueryData(challengeQueryKey, payload);
        break;

      case "participant.update":
        // This event updates a single participant. We must update the cache immutably.
        queryClient.setQueryData<ChallengeDetail>(
          challengeQueryKey,
          (oldData) => {
            if (!oldData) return undefined;

            const updatedAttempt = payload;
            const attemptIndex = oldData.attempts.findIndex(
              (att) => att.user.id === updatedAttempt.user.id
            );

            if (attemptIndex === -1) return oldData;

            const newAttempts = [...oldData.attempts];
            newAttempts[attemptIndex] = {
              ...newAttempts[attemptIndex],
              ...updatedAttempt,
            };

            return { ...oldData, attempts: newAttempts };
          }
        );
        break;

      case "answer.result":
        // Show immediate feedback to the user who answered
        toast(payload.is_correct ? t("correctAnswer") : t("incorrectAnswer"));
        // The score update itself will come via a `participant.update` message.
        break;

      case "error":
        toast.error(payload.detail || t("errorGeneric"));
        break;
    }
  }, [lastMessage, queryClient, challengeQueryKey, t]);

  // Render UI based on connection and data status
  if (isLoading) {
    return <ChallengeSkeletons.RoomSkeleton />;
  }

  if (isError || connectionStatus === "error") {
    return (
      <p className="text-destructive text-center">
        {t("errorLoadingChallenge")}
      </p>
    );
  }

  if (!challengeData) {
    return null; // Or a more specific "not found" message
  }

  // Render different UI based on the challenge status from our single source of truth
  const { status } = challengeData;
  if (status === "pending_invite" || status === "accepted") {
    return (
      <ChallengeLobby
        challenge={challengeData}
        connectionStatus={connectionStatus}
      />
    );
  }
  if (status === "ongoing") {
    return <ChallengeInProgress challenge={challengeData} />;
  }
  if (status === "completed") {
    return <ChallengeResults challenge={challengeData} />;
  }

  return (
    <p>
      {t("unknownChallengeStatus")}: {status}
    </p>
  );
}
