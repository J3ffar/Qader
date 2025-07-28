"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getAdminUserStatistics } from "@/services/api/admin/users.service";
import { queryKeys } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

// Import the reusable view and skeleton
import { StatisticsView } from "@/components/features/platform/study/statistics/StatisticsView";
import { StatisticsDashboardSkeleton } from "@/components/features/platform/study/statistics/StatisticsDashboardSkeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle } from "lucide-react";

interface StatisticsTabProps {
  userId: number;
}

/**
 * This is a "container" component for the admin panel statistics tab.
 * It is responsible for fetching a *specific student's* data and passing it to the reusable StatisticsView.
 */
export function StatisticsTab({ userId }: StatisticsTabProps) {
  const t = useTranslations("Common");

  const { data, isLoading, isError, error } = useQuery({
    // Use the correct query key for a specific admin-viewed user
    queryKey: queryKeys.admin.users.statistics(userId),
    queryFn: () => getAdminUserStatistics(userId),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) return <StatisticsDashboardSkeleton />;

  if (isError) {
    return (
      <Alert variant="destructive" className="mt-6">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>{t("error.title")}</AlertTitle>
        <AlertDescription>
          {getApiErrorMessage(error, t("error.generic"))}
        </AlertDescription>
      </Alert>
    );
  }

  if (!data) {
    // This could happen if the API returns 200 with no data
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>No Statistics Available</AlertTitle>
        <AlertDescription>
          There is no statistical data to display for this student yet.
        </AlertDescription>
      </Alert>
    );
  }

  // Pass the fetched admin data to the same reusable view component.
  return <StatisticsView statistics={data} />;
}
