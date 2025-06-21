"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Check, RefreshCw, Swords, X } from "lucide-react";
import { ChallengeList } from "@/types/api/challenges.types";
import {
  acceptChallenge /* other actions */,
} from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { useAuthStore } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";

interface ChallengeCardProps {
  challenge: ChallengeList;
}

export function ChallengeCard({ challenge }: ChallengeCardProps) {
  const t = useTranslations("Study.challenges");
  const queryClient = useQueryClient();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const isCurrentUserChallenger = user?.id === challenge.challenger.id;
  const opponent = isCurrentUserChallenger
    ? challenge.opponent
    : challenge.challenger;

  const acceptMutation = useMutation({
    mutationFn: () => acceptChallenge(challenge.id),
    onSuccess: () => {
      toast.success(t("challengeAcceptedSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.challenges.lists() as unknown as string[],
      });
      router.push(PATHS.STUDY.CHALLENGE_COLLEAGUES + `/${challenge.id}`);
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });

  // ... define other mutations (decline, cancel, rematch) ...

  const renderStatusBadge = () => {
    switch (challenge.status) {
      case "completed":
        return (
          <Badge variant={challenge.user_is_winner ? "default" : "destructive"}>
            {challenge.user_is_winner ? t("youWon") : t("youLost")}
          </Badge>
        );
      case "pending_invite":
        return <Badge variant="secondary">{t("waitingForOpponent")}</Badge>;
      default:
        return <Badge>{challenge.status_display}</Badge>;
    }
  };

  const renderActions = () => {
    // If it's a pending invite for me
    if (
      challenge.status === "pending_invite" &&
      user?.id === challenge.opponent.id
    ) {
      return (
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => acceptMutation.mutate()}
            disabled={acceptMutation.isPending}
          >
            <Check className="w-4 h-4 ltr:mr-2 rtl:ml-2" /> {t("accept")}
          </Button>
          <Button size="sm" variant="outline">
            <X className="w-4 h-4 ltr:mr-2 rtl:ml-2" /> {t("decline")}
          </Button>
        </div>
      );
    }
    // If it's ongoing
    if (["accepted", "ongoing"].includes(challenge.status)) {
      return (
        <Button
          size="sm"
          onClick={() =>
            router.push(PATHS.STUDY.CHALLENGE_COLLEAGUES + `/${challenge.id}`)
          }
        >
          {t("view")} <ArrowRight className="w-4 h-4 ltr:ml-2 rtl:mr-2" />
        </Button>
      );
    }
    // If completed
    if (challenge.status === "completed") {
      return (
        <Button size="sm" variant="secondary">
          <RefreshCw className="w-4 h-4 ltr:mr-2 rtl:ml-2" />
          {t("rematch")}
        </Button>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardContent className="p-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Avatar>
            <AvatarImage src={opponent.profile_picture || undefined} />
            <AvatarFallback>
              {opponent.username.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="font-semibold">{opponent.username}</p>
            <p className="text-sm text-muted-foreground">
              {challenge.challenge_type_display}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          {renderStatusBadge()}
          {challenge.status === "completed" && (
            <p className="font-bold">
              {challenge.user_score} / {challenge.opponent_score}
            </p>
          )}
        </div>
      </CardContent>
      <CardFooter className="p-4 pt-0 flex justify-end">
        {renderActions()}
      </CardFooter>
    </Card>
  );
}
