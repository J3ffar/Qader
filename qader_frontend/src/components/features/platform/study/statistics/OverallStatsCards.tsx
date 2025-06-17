import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Award, Flame, HelpCircle, Target } from "lucide-react";
import { useTranslations } from "next-intl";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  overallStats: UserStatistics["overall"];
}

export function OverallStatsCards({ overallStats }: Props) {
  const t = useTranslations("Study.statistics.cards");
  const { mastery_level, study_streaks, activity_summary } = overallStats;

  const cardsData = [
    {
      title: t("verbalMastery"),
      value:
        mastery_level.verbal != null
          ? `${mastery_level.verbal.toFixed(1)}%`
          : "N/A",
      description: t("currentLevel"),
      icon: Target,
    },
    {
      title: t("quantMastery"),
      value:
        mastery_level.quantitative != null
          ? `${mastery_level.quantitative.toFixed(1)}%`
          : "N/A",
      description: t("currentLevel"),
      icon: Activity,
    },
    {
      title: t("studyStreak"),
      value: study_streaks.current_days,
      description: t("longestStreak", { count: study_streaks.longest_days }),
      icon: Flame,
    },
    {
      title: t("questionsAnswered"),
      value: `+${activity_summary.total_questions_answered}`,
      description: t("totalThisPeriod"),
      icon: HelpCircle,
    },
    {
      title: t("testsCompleted"),
      value: `+${activity_summary.total_tests_completed}`,
      description: t("totalThisPeriod"),
      icon: Award,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
      {cardsData.map((card, index) => (
        <Card key={index}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
            <p className="text-xs text-muted-foreground">{card.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
