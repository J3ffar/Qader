"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";

import { getChallenges } from "@/services/challenges.service";
import { queryKeys } from "@/constants/queryKeys";
import { ChallengesListSkeleton } from "./ChallengeSkeletons";
import { ChallengeCard } from "./ChallengeCard";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { ChallengeList as IChallengeList } from "@/types/api/challenges.types";

interface FilteredChallengesListProps {
  filter: { status?: string; is_pending_invite_for_user?: boolean };
  emptyMessage: string;
}

export function FilteredChallengesList({
  filter,
  emptyMessage,
}: FilteredChallengesListProps) {
  const t = useTranslations("common");

  // Rationale: This component is self-contained. It fetches, caches, and displays
  // a specific slice of data based on the filter prop. This makes it highly reusable
  // and improves performance by preventing unnecessary re-renders in parent components.
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.challenges.list(filter),
    queryFn: () => getChallenges(filter),
  });

  if (isLoading) {
    return <ChallengesListSkeleton />;
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>{t("error")}</AlertTitle>
        <AlertDescription>{t("errorGeneral")}</AlertDescription>
      </Alert>
    );
  }

  const challenges = data?.results || [];

  if (challenges.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-10">{emptyMessage}</p>
    );
  }

  return (
    <div className="grid gap-4">
      {challenges.map((challenge: IChallengeList) => (
        <ChallengeCard key={challenge.id} challenge={challenge} />
      ))}
    </div>
  );
}
