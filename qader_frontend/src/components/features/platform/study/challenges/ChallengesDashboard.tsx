"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StartChallengeDialog } from "./StartChallengeDialog";
import { FilteredChallengesList } from "./FilteredChallengesList";
import { Swords } from "lucide-react";

export function ChallengesDashboard() {
  const t = useTranslations("Study.challenges");
  const [isCreateDialogOpen, setCreateDialogOpen] = useState(false);

  return (
    <>
      <StartChallengeDialog
        open={isCreateDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Swords className="h-6 w-6" /> {t("myChallenges")}
        </h2>
        <Button onClick={() => setCreateDialogOpen(true)}>
          {t("newChallenge")}
        </Button>
      </div>

      {/* 
        Rationale: Using a controlled Tabs component to manage the active view. 
        Each TabsContent now contains a dedicated component (`FilteredChallengesList`) 
        that fetches only the data it needs. This is more efficient than fetching all
        challenges and filtering on the client, especially with pagination.
      */}
      <Tabs defaultValue="invites" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="invites">{t("pendingInvites")}</TabsTrigger>
          <TabsTrigger value="ongoing">{t("ongoing")}</TabsTrigger>
          <TabsTrigger value="history">{t("history")}</TabsTrigger>
        </TabsList>

        <TabsContent value="invites" className="pt-4">
          <FilteredChallengesList
            filter={{ is_pending_invite_for_user: true }}
            emptyMessage={t("noPendingInvites")}
          />
        </TabsContent>
        <TabsContent value="ongoing" className="pt-4">
          <FilteredChallengesList
            filter={{ status: "ongoing" }}
            emptyMessage={t("noOngoingChallenges")}
          />
        </TabsContent>
        <TabsContent value="history" className="pt-4">
          <FilteredChallengesList
            filter={{ status: "completed" }}
            emptyMessage={t("noHistory")}
          />
        </TabsContent>
      </Tabs>
    </>
  );
}
