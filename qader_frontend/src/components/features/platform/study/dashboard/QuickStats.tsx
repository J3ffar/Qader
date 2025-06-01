import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Flame, Star } from "lucide-react";
import { useTranslations } from "next-intl";

interface QuickStatsProps {
  points: number;
  currentStreakDays: number;
}

export const QuickStats: React.FC<QuickStatsProps> = ({
  points,
  currentStreakDays,
}) => {
  const t = useTranslations("Study.StudyPage.dashboard.quickStats");

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            {t("pointsTitle")}
          </CardTitle>
          <Star className="h-5 w-5 text-yellow-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{points.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">{t("pointsSubtitle")}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            {t("streakTitle")}
          </CardTitle>
          <Flame className="h-5 w-5 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {currentStreakDays} {t("days")}
          </div>
          <p className="text-xs text-muted-foreground">{t("streakSubtitle")}</p>
        </CardContent>
      </Card>
    </div>
  );
};
