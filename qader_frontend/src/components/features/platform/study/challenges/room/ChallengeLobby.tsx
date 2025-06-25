// qader_frontend/src/components/features/platform/study/challenges/room/ChallengeLobby.tsx
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ChallengeDetail } from "@/types/api/challenges.types";
import { ConnectionStatus } from "@/hooks/useWebSocket";
import { useAuthCore } from "@/store/auth.store";
import { markAsReady } from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

// PlayerCard component remains unchanged...
interface PlayerCardProps {
  player: ChallengeDetail["challenger"] | ChallengeDetail["opponent"] | null;
  isReady: boolean;
  isCurrentUser: boolean;
}

const PlayerCard = ({ player, isReady, isCurrentUser }: PlayerCardProps) => {
  if (!player) {
    return (
      <div className="flex flex-col items-center gap-4 text-center p-4 border-2 border-dashed rounded-lg">
        <Avatar className="h-24 w-24">
          <AvatarFallback>?</AvatarFallback>
        </Avatar>
        <p className="font-semibold text-muted-foreground">
          Waiting for opponent...
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 text-center">
      <Avatar className="h-24 w-24 border-4 border-primary">
        <AvatarImage src={player.profile_picture_url || undefined} />
        <AvatarFallback>
          {player.username.charAt(0).toUpperCase()}
        </AvatarFallback>
      </Avatar>
      <p className="text-xl font-bold">
        {player.preferred_name || player.full_name} {isCurrentUser && "(You)"}
      </p>
      {isReady ? (
        <Badge
          variant="default"
          className="gap-2 bg-green-500 hover:bg-green-600"
        >
          <CheckCircle className="h-4 w-4" /> Ready
        </Badge>
      ) : (
        <Badge variant="secondary" className="gap-2">
          <Hourglass className="h-4 w-4 animate-pulse" /> Not Ready
        </Badge>
      )}
    </div>
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

  const readyMutation = useMutation({
    mutationFn: () => markAsReady(challenge.id),
    /**
     * Rationale for the change:
     * Instead of invalidating the query and forcing a refetch (pull), we now perform
     * an immediate local update on the cache. This provides instant UI feedback for the
     * user who clicked the button.
     * We then rely entirely on the `challenge.start` WebSocket event (which is handled in the
     * parent `ChallengeRoom` component) to trigger the actual transition to the game screen.
     * This creates a single, synchronized path for starting the game for both players.
     */
    onSuccess: () => {
      toast.success(t("markedAsReady"));
      // Immediately update the local cache to reflect the user's "ready" state.
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
      // We no longer check for `challenge_started` or invalidate the query here.
      // The `challenge.start` WebSocket event is now the single source of truth for the transition.
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
      <CardContent className="p-6 md:p-8">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] items-center justify-around gap-8">
          <PlayerCard
            player={challenge.challenger}
            isReady={
              challenge.attempts.find(
                (att) => att.user.id === challenge.challenger.id
              )?.is_ready || false
            }
            isCurrentUser={user?.id === challenge.challenger.id}
          />
          <p className="text-5xl font-extrabold text-muted-foreground justify-self-center">
            VS
          </p>
          <PlayerCard
            player={challenge.opponent}
            isReady={
              challenge.attempts.find(
                (att) => att.user.id === challenge.opponent?.id
              )?.is_ready || false
            }
            isCurrentUser={user?.id === challenge.opponent?.id}
          />
        </div>
        <div className="mt-12 text-center">
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
