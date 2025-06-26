"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { useWebSocket } from "@/hooks/useWebSocket";
import { useAuthCore } from "@/store/auth.store";
import { queryKeys } from "@/constants/queryKeys";
import { WS_BASE_URL } from "@/constants/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  acceptChallenge,
  declineChallenge,
} from "@/services/challenges.service";
import { ChallengeDetail } from "@/types/api/challenges.types";

export function WebSocketNotificationHandler() {
  const { isAuthenticated } = useAuthCore();
  const queryClient = useQueryClient();
  const t = useTranslations("Common");

  const [isChallengeInviteOpen, setChallengeInviteOpen] = useState(false);
  const [challengeInvite, setChallengeInvite] =
    useState<ChallengeDetail | null>(null);

  const wsUrl = isAuthenticated
    ? `${WS_BASE_URL}/challenges/notifications/`
    : null;

  const { lastMessage } = useWebSocket(wsUrl, {
    shouldConnect: isAuthenticated,
  });

  useEffect(() => {
    if (!lastMessage) return;

    const invalidateChallengeList = () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.challenges.lists() });
    };

    switch (lastMessage.type) {
      case "new_challenge_invite":
        setChallengeInvite(lastMessage.payload);
        setChallengeInviteOpen(true);
        invalidateChallengeList();
        break;

      case "challenge_accepted_notification":
        toast.success(
          t("Challenges.challengeAcceptedNotif", {
            user: lastMessage.payload.accepted_by,
          })
        );
        invalidateChallengeList();
        break;

      case "challenge_declined_notification":
        toast.warning(
          t("Challenges.challengeDeclinedNotif", {
            user: lastMessage.payload.declined_by,
          })
        );
        invalidateChallengeList();
        break;

      case "challenge_cancelled_notification":
        toast.warning(t("Challenges.challengeCancelledNotif"));
        invalidateChallengeList();
        break;
    }
  }, [lastMessage, queryClient, t]);

  const handleAccept = async () => {
    if (!challengeInvite) return;
    try {
      await acceptChallenge(challengeInvite.id);
      toast.success(t("Challenges.challengeAccepted"));
      setChallengeInviteOpen(false);
    } catch (error) {
      toast.error(t("Challenges.errorAcceptingChallenge"));
    }
  };

  const handleDecline = async () => {
    if (!challengeInvite) return;
    try {
      await declineChallenge(challengeInvite.id);
      toast.warning(t("Challenges.challengeDeclined"));
      setChallengeInviteOpen(false);
    } catch (error) {
      toast.error(t("Challenges.errorDecliningChallenge"));
    }
  };

  return (
    <Dialog open={isChallengeInviteOpen} onOpenChange={setChallengeInviteOpen}>
      <DialogContent>
        <DialogHeader className="items-center">
          <Avatar className="w-20 h-20">
            <AvatarImage
              src={challengeInvite?.challenger.profile_picture_url as string}
            />
            <AvatarFallback>
              {challengeInvite?.challenger.username.charAt(0)}
            </AvatarFallback>
          </Avatar>
          <DialogTitle>{t("Challenges.newChallengeInvite")}</DialogTitle>
          <DialogDescription>
            {challengeInvite?.challenger.full_name}
          </DialogDescription>
          <DialogDescription>
            {t("Challenges.newChallengeInviteDesc", {
              user: challengeInvite?.challenger.username as string,
            })}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button onClick={handleDecline} variant="outline">
            {t("Challenges.decline")}
          </Button>
          <Button onClick={handleAccept}>{t("Challenges.accept")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
