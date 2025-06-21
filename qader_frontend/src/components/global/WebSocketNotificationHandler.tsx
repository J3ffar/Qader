"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { useWebSocket } from "@/hooks/useWebSocket";
import { useAuthCore } from "@/store/auth.store";
import { queryKeys } from "@/constants/queryKeys";
import { WS_BASE_URL } from "@/constants/api";

export function WebSocketNotificationHandler() {
  const { isAuthenticated } = useAuthCore();
  const queryClient = useQueryClient();
  const t = useTranslations("Study.challenges"); // Assuming challenge translations are available

  const wsUrl = isAuthenticated
    ? `${WS_BASE_URL}/challenges/notifications/`
    : null;

  const { lastMessage } = useWebSocket(wsUrl, {
    shouldConnect: isAuthenticated,
  });

  useEffect(() => {
    if (!lastMessage) return;

    // Invalidate the main list query to refresh the UI with new data
    const invalidateChallengeList = () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.challenges.lists() });
    };

    switch (lastMessage.type) {
      case "new_challenge_invite":
        toast.info(t("newChallengeInvite"), {
          // Assuming a new translation key
          description: t("newChallengeInviteDesc", {
            user: lastMessage.payload.challenger.username,
          }),
        });
        invalidateChallengeList();
        break;

      case "challenge_accepted_notification":
        toast.success(
          t("challengeAcceptedNotif", { user: lastMessage.payload.accepted_by })
        );
        invalidateChallengeList();
        break;

      case "challenge_declined_notification":
        toast.warning(
          t("challengeDeclinedNotif", { user: lastMessage.payload.declined_by })
        );
        invalidateChallengeList();
        break;

      case "challenge_cancelled_notification":
        toast.warning(t("challengeCancelledNotif"));
        invalidateChallengeList();
        break;
    }
  }, [lastMessage, queryClient, t]);

  // This component renders nothing
  return null;
}
