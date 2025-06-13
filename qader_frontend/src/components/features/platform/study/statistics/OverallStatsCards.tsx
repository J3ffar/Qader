import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Flame, Target, Trophy } from "lucide-react";
import { useTranslations } from "next-intl";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  overallStats: UserStatistics["overall"];
}

export function OverallStatsCards({ overallStats }: Props) {
  const t = useTranslations("Study.statistics.cards");
  const { mastery_level, study_streaks, activity_summary } = overallStats;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            {t("verbalMastery")}
          </CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {mastery_level.verbal?.toFixed(1) ?? "N/A"}%
          </div>
          <p className="text-xs text-muted-foreground">{t("currentLevel")}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            {t("quantMastery")}
          </CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {mastery_level.quantitative?.toFixed(1) ?? "N/A"}%
          </div>
          <p className="text-xs text-muted-foreground">{t("currentLevel")}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            {t("studyStreak")}
          </CardTitle>
          <Flame className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{study_streaks.current_days}</div>
          <p className="text-xs text-muted-foreground">
            {t("consecutiveDays", { count: study_streaks.current_days })}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            {t("testsCompleted")}
          </CardTitle>
          <Trophy className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            +{activity_summary.total_tests_completed}
          </div>
          <p className="text-xs text-muted-foreground">
            {t("totalThisPeriod")}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
