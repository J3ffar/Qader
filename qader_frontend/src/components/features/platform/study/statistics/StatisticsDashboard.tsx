"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { AlertTriangle } from "lucide-react";

import { getUserStatistics } from "@/services/study.service";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { StatisticsDashboardSkeleton } from "./StatisticsDashboardSkeleton";
import { PerformanceTrendsChart } from "./PerformanceTrendsChart";
import { SectionPerformanceBreakdown } from "./SectionPerformanceBreakdown";
import { OverallStatsCards } from "./OverallStatsCards";
import { TimeAnalyticsCard } from "./TimeAnalyticsCard";
import { AverageScoresByTypeCard } from "./AverageScoresByTypeCard";
import { ActionableInsightsTabs } from "./ActionableInsightsTabs";
import { queryKeys } from "@/constants/queryKeys";

export function StatisticsDashboard() {
  const t = useTranslations("Common");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: queryKeys.study.statistics({
      TODO: "pass time of the statistics",
    }),
    queryFn: () => getUserStatistics(),
    retry: 1,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
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
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Row 1: Key Stats Cards - Full Width */}
      <OverallStatsCards overallStats={data.overall} />

      {/* Row 2: Main Chart - Full Width */}
      <PerformanceTrendsChart trends={data.performance_trends_by_test_type} />

      {/* Grid for subsequent multi-column rows */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Row 3: Detailed Breakdowns */}
        <div className="lg:col-span-7">
          <SectionPerformanceBreakdown
            performance={data.performance_by_section}
          />
        </div>
        <div className="lg:col-span-5">
          <ActionableInsightsTabs
            skills={data.skill_proficiency_summary}
            tests={data.test_history_summary}
          />
        </div>

        {/* Row 4: Summaries & Secondary Analytics */}
        <div className="lg:col-span-7">
          <AverageScoresByTypeCard
            scoresByType={data.average_scores_by_test_type}
          />
        </div>
        <div className="lg:col-span-5">
          <TimeAnalyticsCard timeAnalytics={data.time_analytics} />
        </div>
      </div>
    </div>
  );
}
