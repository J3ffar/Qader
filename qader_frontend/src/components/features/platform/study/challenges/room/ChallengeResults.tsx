"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Crown, Gamepad2, ThumbsDown, Trophy, Home } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ChallengeDetail } from "@/types/api/challenges.types";
import { useAuthCore } from "@/store/auth.store";
import { createRematch } from "@/services/challenges.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { PATHS } from "@/constants/paths";

export function ChallengeResults({
  challenge,
}: {
  challenge: ChallengeDetail;
}) {
  const t = useTranslations("Study.challenges");
  const { user } = useAuthCore();
  const router = useRouter();

  const rematchMutation = useMutation({
    mutationFn: () => createRematch(challenge.id),
    onSuccess: (newChallenge) => {
      toast.success(t("rematchSent"));
      router.push(`${PATHS.STUDY.CHALLENGE_COLLEAGUES}/${newChallenge.id}`);
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, t("errorGeneric"))),
  });

  const isWinner = challenge.winner?.id === user?.id;
  const isDraw = !challenge.winner;

  const ResultIcon = isDraw ? Gamepad2 : isWinner ? Trophy : ThumbsDown;
  const resultText = isDraw ? t("draw") : isWinner ? t("youWon") : t("youLost");
  const resultColor = isDraw
    ? "text-primary"
    : isWinner
    ? "text-green-500"
    : "text-destructive";

  const opponent =
    user?.id === challenge.challenger.id
      ? challenge.opponent
      : challenge.challenger;

  return (
    <Card className="w-full max-w-2xl mx-auto text-center animate-fade-in">
      <CardHeader>
        <ResultIcon className={`mx-auto h-16 w-16 ${resultColor}`} />
        <CardTitle className={`text-4xl font-bold ${resultColor}`}>
          {resultText}
        </CardTitle>
        <CardDescription>{t("challengeOver")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex justify-around items-center">
          <div className="flex flex-col items-center gap-2">
            <Avatar className="h-20 w-20">
              <AvatarImage src={user?.profile_picture_url as string} />
              <AvatarFallback>
                {user?.username.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <p className="font-semibold">{user?.username}</p>
            <p className="text-3xl font-bold">{challenge.user_score}</p>
          </div>

          <p className="text-4xl font-bold text-muted-foreground">VS</p>

          <div className="flex flex-col items-center gap-2">
            <Avatar className="h-20 w-20">
              <AvatarImage src={opponent?.profile_picture as string} />
              <AvatarFallback>
                {opponent?.username.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <p className="font-semibold">{opponent?.username}</p>
            <p className="text-3xl font-bold">{challenge.opponent_score}</p>
          </div>
        </div>
        <div className="flex justify-center gap-4 pt-4">
          <Button
            onClick={() => rematchMutation.mutate()}
            disabled={rematchMutation.isPending}
          >
            <Gamepad2 className="mr-2 h-4 w-4" />
            {t("rematch")}
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push(PATHS.STUDY.CHALLENGE_COLLEAGUES)}
          >
            <Home className="mr-2 h-4 w-4" />
            {t("backToHub")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
