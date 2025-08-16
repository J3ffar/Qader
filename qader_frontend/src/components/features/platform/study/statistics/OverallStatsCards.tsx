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
      gradient: "from-emerald-500 to-teal-600",
      bgColor: "bg-gradient-to-br from-emerald-50 to-teal-50",
      iconBg: "bg-emerald-100",
      iconColor: "text-emerald-600",
      valueColor: "text-emerald-700",
      borderColor: "border-emerald-200",
    },
    {
      title: t("quantMastery"),
      value:
        mastery_level.quantitative != null
          ? `${mastery_level.quantitative.toFixed(1)}%`
          : "N/A",
      description: t("currentLevel"),
      icon: Activity,
      gradient: "from-blue-500 to-indigo-600",
      bgColor: "bg-gradient-to-br from-blue-50 to-indigo-50",
      iconBg: "bg-blue-100",
      iconColor: "text-blue-600",
      valueColor: "text-blue-700",
      borderColor: "border-blue-200",
    },
    {
      title: t("studyStreak"),
      value: study_streaks.current_days,
      description: t("longestStreak", { count: study_streaks.longest_days }),
      icon: Flame,
      gradient: "from-orange-500 to-red-500",
      bgColor: "bg-gradient-to-br from-orange-50 to-red-50",
      iconBg: "bg-orange-100",
      iconColor: "text-orange-600",
      valueColor: "text-orange-700",
      borderColor: "border-orange-200",
    },
    {
      title: t("questionsAnswered"),
      value: `+${activity_summary.total_questions_answered}`,
      description: t("totalThisPeriod"),
      icon: HelpCircle,
      gradient: "from-purple-500 to-pink-600",
      bgColor: "bg-gradient-to-br from-purple-50 to-pink-50",
      iconBg: "bg-purple-100",
      iconColor: "text-purple-600",
      valueColor: "text-purple-700",
      borderColor: "border-purple-200",
    },
    {
      title: t("testsCompleted"),
      value: `+${activity_summary.total_tests_completed}`,
      description: t("totalThisPeriod"),
      icon: Award,
      gradient: "from-amber-500 to-yellow-600",
      bgColor: "bg-gradient-to-br from-amber-50 to-yellow-50",
      iconBg: "bg-amber-100",
      iconColor: "text-amber-600",
      valueColor: "text-amber-700",
      borderColor: "border-amber-200",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-5">
      {cardsData.map((card, index) => (
        <Card 
          key={index} 
          className={`relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${card.bgColor} ${card.borderColor} border-2`}
        >
          {/* Gradient accent bar */}
          <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${card.gradient}`} />
          
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle className="text-sm font-medium text-gray-700">
              {card.title}
            </CardTitle>
            <div className={`p-2 rounded-full ${card.iconBg}`}>
              <card.icon className={`h-5 w-5 ${card.iconColor}`} />
            </div>
          </CardHeader>
          
          <CardContent>
            <div className={`text-2xl font-bold ${card.valueColor} mb-1`}>
              {card.value}
            </div>
            <p className="text-xs text-gray-600">
              {card.description}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
