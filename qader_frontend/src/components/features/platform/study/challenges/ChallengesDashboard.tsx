"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChallengesList } from "./ChallengesList";
import { StartChallengeDialog } from "./StartChallengeDialog";
import { ChallengesListSkeleton } from "./ChallengeSkeletons";
import { queryKeys } from "@/constants/queryKeys";
import { getChallenges } from "@/services/challenges.service";
import { useAuthStore } from "@/store/auth.store"; // Assuming you have an auth store to get current user

export function ChallengesDashboard() {
  const t = useTranslations("Study.challenges");
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user); // Get current user to filter invites
  const [isCreateDialogOpen, setCreateDialogOpen] = useState(false);

  const {
    data: challengesData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.challenges.list({}),
    queryFn: () => getChallenges(),
    staleTime: 1000 * 60, // 1 minute
  });

  const challenges = challengesData?.results || [];

  const pendingInvites = challenges.filter(
    (c) => c.status === "pending_invite" && c.opponent.id === user?.id
  );
  const ongoing = challenges.filter((c) =>
    ["accepted", "ongoing"].includes(c.status)
  );
  const history = challenges.filter((c) =>
    ["completed", "declined", "cancelled", "expired"].includes(c.status)
  );

  if (isLoading) {
    return <ChallengesListSkeleton />;
  }

  if (isError) {
    return <p className="text-center text-destructive">{t("errorGeneric")}</p>;
  }

  return (
    <>
      <StartChallengeDialog
        open={isCreateDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />

      <div className="flex justify-end rtl:justify-start mb-4">
        <Button onClick={() => setCreateDialogOpen(true)}>
          {t("newChallenge")}
        </Button>
      </div>

      <Tabs defaultValue="invites" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="invites">{t("pendingInvites")}</TabsTrigger>
          <TabsTrigger value="ongoing">{t("ongoing")}</TabsTrigger>
          <TabsTrigger value="history">{t("history")}</TabsTrigger>
        </TabsList>
        <TabsContent value="invites">
          <ChallengesList
            challenges={pendingInvites}
            emptyMessage={t("noPendingInvites")}
          />
        </TabsContent>
        <TabsContent value="ongoing">
          <ChallengesList
            challenges={ongoing}
            emptyMessage={t("noOngoingChallenges")}
          />
        </TabsContent>
        <TabsContent value="history">
          <ChallengesList challenges={history} emptyMessage={t("noHistory")} />
        </TabsContent>
      </Tabs>
    </>
  );
}
