// qader_frontend/src/components/features/platform/study/challenges/room/ChallengeLobby.tsx
"use client";

import { useTranslations } from "next-intl";
import { CheckCircle, Hourglass, Loader2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChallengeHeader } from "./ChallengeHeader";
import { ChallengeDetail } from "@/types/api/challenges.types";
import { ConnectionStatus } from "@/hooks/useWebSocket";
import { useAuthCore } from "@/store/auth.store";

// Helper component for status display remains useful
const PlayerStatus = ({
  isReady,
  label,
}: {
  isReady: boolean;
  label: string;
}) => {
  return isReady ? (
    <Badge variant="default" className="gap-2 bg-green-500 hover:bg-green-600">
      <CheckCircle className="h-4 w-4" /> {label}
    </Badge>
  ) : (
    <Badge variant="secondary" className="gap-2">
      <Hourglass className="h-4 w-4 animate-pulse" /> {label}
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

  const currentUserAttempt = challenge.attempts.find(
    (att) => att.user.id === user?.id
  );
  const opponentAttempt = challenge.attempts.find(
    (att) => att.user.id !== user?.id
  );
  const getConnectionStatusText = (status: ConnectionStatus): string => {
    switch (status) {
      case "connecting":
        return t("connection.connecting");
      case "open":
        return t("connection.connected");
      case "closed":
        return t("connection.disconnected");
      // case "reconnecting":
      //   return t("connection.reconnecting");
      default:
        return t("connection.error");
    }
  };

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
          {/* Use the new function here */}
          {getConnectionStatusText(connectionStatus)}
        </Badge>
      </CardHeader>
      <CardContent className="p-6 md:p-8 space-y-8">
        <ChallengeHeader challenge={challenge} />

        <div className="flex justify-around items-center">
          <PlayerStatus
            isReady={currentUserAttempt?.is_ready || false}
            label={t(
              currentUserAttempt?.is_ready ? "youAreReady" : "gettingYouReady"
            )}
          />
          <div />
          <PlayerStatus
            isReady={opponentAttempt?.is_ready || false}
            label={t(
              opponentAttempt?.is_ready
                ? "opponentIsReady"
                : "waitingForOpponent"
            )}
          />
        </div>

        <div className="mt-8 text-center h-10">
          {bothPlayersReady && (
            <div className="flex items-center justify-center gap-2 text-xl font-semibold text-primary animate-fade-in">
              <Loader2 className="h-6 w-6 animate-spin" />
              <p>{t("startingChallenge")}</p>
            </div>
          )}
          {!bothPlayersReady && !opponentAttempt?.is_ready && (
            <div className="flex items-center justify-center gap-2 text-lg font-semibold text-muted-foreground animate-pulse">
              <p>{t("waitingForOpponent")}...</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
