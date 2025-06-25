// src/components/features/platform/study/challenges/ChallengeCard.tsx
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight,
  Check,
  RefreshCw,
  Swords,
  X,
  Ban,
  Gamepad2,
} from "lucide-react";
import { ChallengeList } from "@/types/api/challenges.types";
import {
  acceptChallenge,
  declineChallenge,
  cancelChallenge,
  createRematch,
  markAsReady,
} from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { useAuthCore } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";

interface ChallengeCardProps {
  challenge: ChallengeList;
}

export function ChallengeCard({ challenge }: ChallengeCardProps) {
  const t = useTranslations("Study.challenges");
  const queryClient = useQueryClient();
  const router = useRouter();
  const { user } = useAuthCore();

  const isCurrentUserChallenger = user?.id === challenge.challenger.id;
  const opponent = isCurrentUserChallenger
    ? challenge.opponent
    : challenge.challenger;
  const currentUser = isCurrentUserChallenger
    ? challenge.challenger
    : challenge.opponent;

  const invalidateLists = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.challenges.lists() });

  const acceptMutation = useMutation({
    mutationFn: () => acceptChallenge(challenge.id),
    onSuccess: (acceptedChallenge) => {
      toast.promise(markAsReady(acceptedChallenge.id), {
        loading: t("acceptingAndPreparing"),
        success: () => {
          invalidateLists();
          router.push(
            `${PATHS.STUDY.CHALLENGE_COLLEAGUES}/${acceptedChallenge.id}`
          );
          return t("challengeAcceptedAndReady");
        },
        error: (err) => getApiErrorMessage(err, t("errorGeneric")),
      });
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, t("errorGeneric"))),
  });

  const declineMutation = useMutation({
    mutationFn: () => declineChallenge(challenge.id),
    onSuccess: () => {
      toast.success(t("challengeDeclined"));
      invalidateLists();
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, t("errorGeneric"))),
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelChallenge(challenge.id),
    onSuccess: () => {
      toast.success(t("challengeCancelled"));
      invalidateLists();
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, t("errorGeneric"))),
  });

  const rematchMutation = useMutation({
    mutationFn: () => createRematch(challenge.id),
    onSuccess: (newChallenge) => {
      toast.promise(markAsReady(newChallenge.id), {
        loading: t("creatingAndPreparing"),
        success: () => {
          invalidateLists();
          router.push(`${PATHS.STUDY.CHALLENGE_COLLEAGUES}/${newChallenge.id}`);
          return t("rematchSentAndReady");
        },
        error: (err) => getApiErrorMessage(err, t("errorGeneric")),
      });
    },
    onError: (error) =>
      toast.error(getApiErrorMessage(error, t("errorGeneric"))),
  });

  const renderStatusBadge = () => {
    if (challenge.status === "completed") {
      if (challenge.user_is_winner === null)
        return <Badge variant="secondary">{t("draw")}</Badge>;
      return (
        <Badge variant={challenge.user_is_winner ? "default" : "destructive"}>
          {challenge.user_is_winner ? t("youWon") : t("youLost")}
        </Badge>
      );
    }
    if (challenge.status === "pending_invite") {
      return (
        <Badge variant="secondary">
          {isCurrentUserChallenger ? t("inviteSent") : t("pendingForYou")}
        </Badge>
      );
    }
    if (challenge.status === "ongoing" || challenge.status === "accepted") {
      return (
        <Badge className="bg-blue-500 hover:bg-blue-600">{t("ongoing")}</Badge>
      );
    }
    return <Badge variant="outline">{challenge.status_display}</Badge>;
  };

  const renderActions = () => {
    if (challenge.status === "pending_invite") {
      if (!isCurrentUserChallenger) {
        // It's an invite for me
        return (
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => acceptMutation.mutate()}
              loading={acceptMutation.isPending}
            >
              <Check className="w-4 h-4 ltr:mr-2 rtl:ml-2" /> {t("accept")}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => declineMutation.mutate()}
              loading={declineMutation.isPending}
            >
              <X className="w-4 h-4 ltr:mr-2 rtl:ml-2" /> {t("decline")}
            </Button>
          </div>
        );
      }
      return (
        // I sent the invite
        <Button
          size="sm"
          variant="destructive-outline"
          onClick={() => cancelMutation.mutate()}
          loading={cancelMutation.isPending}
        >
          <Ban className="w-4 h-4 ltr:mr-2 rtl:ml-2" /> {t("cancel")}
        </Button>
      );
    }
    if (["accepted", "ongoing"].includes(challenge.status)) {
      return (
        <Button
          size="sm"
          onClick={() =>
            router.push(`${PATHS.STUDY.CHALLENGE_COLLEAGUES}/${challenge.id}`)
          }
        >
          {t("view")} <ArrowRight className="w-4 h-4 ltr:ml-2 rtl:mr-2" />
        </Button>
      );
    }
    if (challenge.status === "completed") {
      return (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => rematchMutation.mutate()}
          loading={rematchMutation.isPending}
        >
          <RefreshCw className="w-4 h-4 ltr:mr-2 rtl:ml-2" /> {t("rematch")}
        </Button>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 font-semibold">
          <Avatar className="h-10 w-10">
            <AvatarImage src={currentUser?.profile_picture_url || undefined} />
            <AvatarFallback>
              {currentUser?.username.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <span>{t("you")}</span>
          <span className="text-muted-foreground mx-1">vs</span>
          <Avatar className="h-10 w-10">
            <AvatarImage src={opponent.profile_picture_url || undefined} />
            <AvatarFallback>
              {opponent.username.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <span>{opponent.username}</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            {renderStatusBadge()}
            <p className="text-sm text-muted-foreground mt-1">
              {challenge.challenge_type_display}
            </p>
          </div>
          {challenge.status === "completed" && (
            <p className="text-2xl font-bold">
              <span className={challenge.user_is_winner ? "text-primary" : ""}>
                {challenge.user_score}
              </span>
              <span className="text-muted-foreground mx-1">-</span>
              <span>{challenge.opponent_score}</span>
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
