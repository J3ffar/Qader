"use client";

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { getChallengeDetails } from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { useWebSocket } from "@/hooks/useWebSocket";
import {
  ChallengeDetail,
  ChallengeAttempt,
} from "@/types/api/challenges.types";
import { WS_BASE_URL } from "@/constants/api";
import { useAuthCore } from "@/store/auth.store";

import { ChallengeLobby } from "./room/ChallengeLobby";
import { ChallengeInProgress } from "./room/ChallengeInProgress";
import { ChallengeResults } from "./room/ChallengeResults";
import { ChallengeSkeletons } from "./ChallengeSkeletons";

interface ChallengeRoomProps {
  challengeId: string;
}

export function ChallengeRoom({ challengeId }: ChallengeRoomProps) {
  const t = useTranslations("Study.challenges");
  const queryClient = useQueryClient();
  const { user } = useAuthCore();
  const challengeQueryKey = queryKeys.challenges.detail(challengeId);

  const {
    data: challengeData,
    isLoading,
    isError,
    error,
  } = useQuery<ChallengeDetail>({
    queryKey: challengeQueryKey,
    queryFn: () => getChallengeDetails(challengeId),
    staleTime: Infinity, // Data will be kept fresh by WebSockets
    retry: false, // Don't retry on 403/404, handle error gracefully
  });

  const wsUrl = user ? `${WS_BASE_URL}/challenges/${challengeId}/` : null;
  const { lastMessage, connectionStatus } = useWebSocket(wsUrl, {
    shouldConnect: !!challengeId && !!user,
  });

  useEffect(() => {
    if (!lastMessage) return;

    console.log("WebSocket Message Received:", lastMessage);
    const { type, payload } = lastMessage;
    // Rationale: This switch statement is now the central hub for real-time updates.
    // It directly manipulates the TanStack Query cache, ensuring the UI always reflects
    // the true state of the challenge without needing manual state management.
    switch (type) {
      case "challenge.update":
      case "challenge.start":
      case "challenge.end":
        // Full state updates, replace the cache entirely.
        queryClient.setQueryData(challengeQueryKey, payload);
        if (type === "challenge.start") toast.success(t("challengeStarted"));
        if (type === "challenge.end") toast.info(t("challengeOver"));
        break;

      case "participant.update":
        // Granular update for a single participant's state (e.g., is_ready, score).
        queryClient.setQueryData<ChallengeDetail>(
          challengeQueryKey,
          (oldData) => {
            if (!oldData) return undefined;
            const updatedAttempt = payload as ChallengeAttempt;
            const newAttempts = oldData.attempts.map((att) =>
              att.user.id === updatedAttempt.user.id ? updatedAttempt : att
            );
            return { ...oldData, attempts: newAttempts };
          }
        );
        break;

      case "answer.result":
        // Immediate feedback toast when an answer is submitted by ANY player.
        // We only show the "correct/incorrect" toast to the user who answered.
        if (payload.user_id === user?.id) {
          toast.info(
            payload.is_correct ? t("correctAnswer") : t("incorrectAnswer")
          );
        }
        break;

      case "error":
        toast.error(payload.detail || t("errorGeneric"));
        break;
    }
  }, [lastMessage, queryClient, challengeQueryKey, t, user?.id]);

  if (isLoading) {
    return <ChallengeSkeletons.RoomSkeleton />;
  }

  if (isError) {
    return (
      <div className="text-center py-10">
        <p className="text-lg font-semibold text-destructive">
          {t("errorLoadingChallenge")}
        </p>
        <p className="text-muted-foreground">{error.message}</p>
      </div>
    );
  }

  if (connectionStatus === "connecting") {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-muted-foreground">{t("connectingToChallenge")}</p>
      </div>
    );
  }

  if (!challengeData) {
    return null; // Should be handled by isError
  }

  // Render different UI based on the challenge status from our single source of truth (TanStack Query cache)
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
    <p className="text-center py-10">
      {t("unknownChallengeStatus")}: {status}
    </p>
  );
}
