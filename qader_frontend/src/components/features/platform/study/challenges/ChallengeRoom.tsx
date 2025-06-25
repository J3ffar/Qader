// qader_frontend/src/components/features/platform/study/challenges/ChallengeRoom.tsx
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
  ChallengeState,
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
    staleTime: Infinity,
    retry: false,
  });

  const wsUrl = user ? `${WS_BASE_URL}/challenges/${challengeId}/` : null;
  const { lastMessage, connectionStatus } = useWebSocket(wsUrl, {
    shouldConnect: !!challengeId && !!user,
  });

  useEffect(() => {
    if (!lastMessage) return;

    console.log("WebSocket Message Received:", lastMessage);
    const { type, payload } = lastMessage;

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
        queryClient.setQueryData<ChallengeState>(
          challengeQueryKey,
          (oldData) => {
            if (!oldData) return undefined;

            // Update score
            const newAttempts = oldData.attempts.map((att) =>
              att.user.id === payload.user_id
                ? { ...att, score: payload.current_score }
                : att
            );

            // Update who has answered the question
            const currentAnswers =
              oldData.answeredBy?.[payload.question_id] || [];
            const newAnsweredBy = {
              ...oldData.answeredBy,
              [payload.question_id]: [...currentAnswers, payload.user_id],
            };

            // Notify current user only
            if (payload.user_id === user?.id) {
              toast.info(
                payload.is_correct ? t("correctAnswer") : t("incorrectAnswer")
              );
            } else {
              toast.info(t("opponentAnswered"));
            }

            return {
              ...oldData,
              attempts: newAttempts,
              answeredBy: newAnsweredBy,
              lastAnsweredBy: payload.user_id, // Track who answered last for UI effects
            };
          }
        );
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
    return null;
  }

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
    // Rationale: Pass the challenge config to enable the timer
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
