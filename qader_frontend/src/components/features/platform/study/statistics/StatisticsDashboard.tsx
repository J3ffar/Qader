"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { AlertTriangle } from "lucide-react";

import { getUserStatistics } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { StatisticsDashboardSkeleton } from "./StatisticsDashboardSkeleton";
import { PerformanceTrendsChart } from "./PerformanceTrendsChart";
import { SectionPerformanceBreakdown } from "./SectionPerformanceBreakdown";
import { OverallStatsCards } from "./OverallStatsCards";
import { TimeAnalyticsCard } from "./TimeAnalyticsCard";
import { ActionableInsightsTabs } from "./ActionableInsightsTabs"; // New component

export function StatisticsDashboard() {
  const t = useTranslations("Common");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: [QUERY_KEYS.USER_STATISTICS],
    queryFn: () => getUserStatistics(),
    retry: 1,
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
          {t("error.generic")}
          <br />
          <Button onClick={() => refetch()} variant="link" className="p-0">
            {t("error.retry")}
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!data) {
    return null; // Should be covered by isLoading/isError, but a safe fallback.
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      {/* Row 1: Key Stats Cards - Full Width */}
      <div className="lg:col-span-12">
        <OverallStatsCards overallStats={data.overall} />
      </div>

      {/* Row 2: Main Chart and Side Widgets */}
      {/* Main Chart takes up 8/12 columns on large screens */}
      <div className="lg:col-span-8">
        <PerformanceTrendsChart trends={data.performance_trends_by_test_type} />
      </div>

      {/* Side widgets take up 4/12 columns */}
      <div className="space-y-6 lg:col-span-4">
        <TimeAnalyticsCard timeAnalytics={data.time_analytics} />
        <ActionableInsightsTabs
          skills={data.skill_proficiency_summary}
          tests={data.test_history_summary}
        />
      </div>

      {/* Row 3: Full-width detailed breakdown */}
      <div className="lg:col-span-12">
        <SectionPerformanceBreakdown
          performance={data.performance_by_section}
        />
      </div>
    </div>
  );
}
