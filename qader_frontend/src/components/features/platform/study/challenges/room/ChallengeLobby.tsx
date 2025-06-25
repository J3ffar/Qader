// src/components/features/platform/study/challenges/room/ChallengeLobby.tsx
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { CheckCircle, Hourglass, Loader2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChallengeHeader } from "./ChallengeHeader";
import { ChallengeDetail } from "@/types/api/challenges.types";
import { ConnectionStatus } from "@/hooks/useWebSocket";
import { useAuthCore } from "@/store/auth.store";
import { markAsReady } from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

const PlayerStatus = ({
  isReady,
  isOpponent,
}: {
  isReady: boolean;
  isOpponent: boolean;
}) => {
  const t = useTranslations("Study.challenges");
  return isReady ? (
    <Badge variant="default" className="gap-2 bg-green-500 hover:bg-green-600">
      <CheckCircle className="h-4 w-4" />{" "}
      {isOpponent ? t("opponentIsReady") : t("readyButton")}
    </Badge>
  ) : (
    <Badge variant="secondary" className="gap-2">
      <Hourglass className="h-4 w-4 animate-pulse" /> {t("waiting")}
    </Badge>
  );
};

interface ChallengeLobbyProps {
  challenge: ChallengeDetail;
  connectionStatus: ConnectionStatus;
}

export function ChallengeLobby({
  challenge,
  connectionStatus,
}: ChallengeLobbyProps) {
  const t = useTranslations("Study.challenges");
  const { user } = useAuthCore();
  const queryClient = useQueryClient();
  const challengeQueryKey = queryKeys.challenges.detail(challenge.id);

  const currentUserAttempt = challenge.attempts.find(
    (att) => att.user.id === user?.id
  );
  const opponentAttempt = challenge.attempts.find(
    (att) => att.user.id !== user?.id
  );

  const readyMutation = useMutation({
    mutationFn: () => markAsReady(challenge.id),
    onSuccess: () => {
      toast.success(t("markedAsReady"));
      queryClient.setQueryData<ChallengeDetail>(
        challengeQueryKey,
        (oldData) => {
          if (!oldData) return undefined;
          return {
            ...oldData,
            attempts: oldData.attempts.map((att) =>
              att.user.id === user?.id ? { ...att, is_ready: true } : att
            ),
          };
        }
      );
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, t("errorGeneric"))),
  });

  const bothPlayersReady =
    challenge.attempts.length === 2 &&
    challenge.attempts.every((att) => att.is_ready);

  return (
    <Card className="w-full max-w-4xl mx-auto animate-fade-in">
      <CardHeader className="text-center">
        <CardTitle className="text-3xl">{t("challengeLobbyTitle")}</CardTitle>
        <CardDescription>{challenge.challenge_type_display}</CardDescription>
        <Badge
          variant={connectionStatus === "open" ? "default" : "destructive"}
          className="mx-auto mt-2"
        >
          {connectionStatus}
        </Badge>
      </CardHeader>
      <CardContent className="p-6 md:p-8 space-y-8">
        <ChallengeHeader challenge={challenge} />

        <div className="flex justify-around items-center">
          <PlayerStatus
            isReady={currentUserAttempt?.is_ready || false}
            isOpponent={false}
          />
          <div></div>
          <PlayerStatus
            isReady={opponentAttempt?.is_ready || false}
            isOpponent={true}
          />
        </div>

        <div className="mt-8 text-center">
          {bothPlayersReady ? (
            <div className="flex items-center justify-center gap-2 text-xl font-semibold text-primary">
              <Loader2 className="h-6 w-6 animate-spin" />
              <p>{t("startingChallenge")}</p>
            </div>
          ) : (
            <Button
              size="lg"
              onClick={() => readyMutation.mutate()}
              disabled={currentUserAttempt?.is_ready || readyMutation.isPending}
            >
              {readyMutation.isPending && (
                <Loader2 className="ltr:mr-2 rtl:ml-2 h-4 w-4 animate-spin" />
              )}
              {currentUserAttempt?.is_ready
                ? t("waitingForOpponent")
                : t("readyButton")}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
