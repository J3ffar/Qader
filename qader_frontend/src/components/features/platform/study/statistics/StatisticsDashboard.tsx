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
import { SkillProficiencyLists } from "./SkillProficiencyLists";
import { RecentTestsTable } from "./RecentTestsTable";

export function StatisticsDashboard() {
  const t = useTranslations("Common");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: [QUERY_KEYS.USER_STATISTICS],
    queryFn: () => getUserStatistics(), // Fetch without aggregation for most detailed trend chart
    retry: 1,
  });

  if (isLoading) {
    return <StatisticsDashboardSkeleton />;
  }

  if (isError) {
    // Error handling remains the same
  }

  // A check to ensure we have data before rendering
  if (!data) {
    return null; // Or some fallback UI
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* Main Column */}
      <div className="space-y-6 lg:col-span-2">
        <PerformanceTrendsChart trends={data.performance_trends_by_test_type} />
        <SectionPerformanceBreakdown
          performance={data.performance_by_section}
        />
      </div>

      {/* Sidebar Column */}
      <div className="space-y-6 lg:col-span-1">
        <OverallStatsCards overallStats={data.overall} />
        <TimeAnalyticsCard timeAnalytics={data.time_analytics} />
        <SkillProficiencyLists skills={data.skill_proficiency_summary} />
        <RecentTestsTable tests={data.test_history_summary} />
      </div>
    </div>
  );
}
