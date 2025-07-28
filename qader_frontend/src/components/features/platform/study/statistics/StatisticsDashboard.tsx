"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { AlertTriangle } from "lucide-react";

import { getUserStatistics } from "@/services/study.service";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { StatisticsDashboardSkeleton } from "./StatisticsDashboardSkeleton";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { StatisticsView } from "./StatisticsView"; // KEY CHANGE: Import the new view component

/**
 * This is now a "container" component for the student-facing statistics page.
 * It is responsible for fetching the student's own data and passing it to the reusable StatisticsView.
 */
export function StatisticsDashboard() {
  const t = useTranslations("Common");

  // Data fetching logic remains the same
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: queryKeys.study.statistics({}), // Assuming simple key for current user
    queryFn: () => getUserStatistics(),
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) {
    return <StatisticsDashboardSkeleton />;
  }

  if (isError) {
    return (
      <Alert variant="destructive" className="mt-6">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>{t("error.title")}</AlertTitle>
        <AlertDescription>
          {getApiErrorMessage(error, t("error.generic"))}
          <br />
          <Button onClick={() => refetch()} variant="link" className="p-0">
            {t("error.retry")}
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!data) {
    return null;
  }

  // KEY CHANGE: The complex JSX is replaced with a single call to the reusable view component.
  return <StatisticsView statistics={data} />;
}
