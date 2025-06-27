"use client";

import { UserStatistics } from "@/types/api/study.types";
import { PerformanceTrendsChart } from "./PerformanceTrendsChart";
import { SectionPerformanceBreakdown } from "./SectionPerformanceBreakdown";
import { OverallStatsCards } from "./OverallStatsCards";
import { TimeAnalyticsCard } from "./TimeAnalyticsCard";
import { AverageScoresByTypeCard } from "./AverageScoresByTypeCard";
import { ActionableInsightsTabs } from "./ActionableInsightsTabs";

interface StatisticsViewProps {
  statistics: UserStatistics;
}

/**
 * A purely presentational component for displaying user statistics.
 * It accepts the full statistics object as a prop and handles the layout.
 * This component is reused by both the student-facing dashboard and the admin panel.
 */
export function StatisticsView({ statistics }: StatisticsViewProps) {
  return (
    <div className="space-y-6">
      {/* Row 1: Key Stats Cards - Full Width */}
      <OverallStatsCards overallStats={statistics.overall} />

      {/* Row 2: Main Chart - Full Width */}
      <PerformanceTrendsChart
        trends={statistics.performance_trends_by_test_type}
      />

      {/* Grid for subsequent multi-column rows */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Row 3: Detailed Breakdowns */}
        <div className="lg:col-span-7">
          <SectionPerformanceBreakdown
            performance={statistics.performance_by_section}
          />
        </div>
        <div className="lg:col-span-5">
          <ActionableInsightsTabs
            skills={statistics.skill_proficiency_summary}
            tests={statistics.test_history_summary}
          />
        </div>

        {/* Row 4: Summaries & Secondary Analytics */}
        <div className="lg:col-span-7">
          <AverageScoresByTypeCard
            scoresByType={statistics.average_scores_by_test_type}
          />
        </div>
        <div className="lg:col-span-5">
          <TimeAnalyticsCard timeAnalytics={statistics.time_analytics} />
        </div>
      </div>
    </div>
  );
}
