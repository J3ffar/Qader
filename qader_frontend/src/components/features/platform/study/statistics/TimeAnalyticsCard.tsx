"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, Clock, XCircle } from "lucide-react";
import { useTranslations } from "next-intl";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  timeAnalytics: UserStatistics["time_analytics"];
}

const formatSeconds = (seconds: number | null): string => {
  if (seconds === null) return "N/A";
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
};

export function TimeAnalyticsCard({ timeAnalytics }: Props) {
  const t = useTranslations("Study.statistics.timeAnalytics");
  const { average_time_per_question_by_correctness: correctnessTime } =
    timeAnalytics;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-green-500" />
            <p className="text-sm font-medium">{t("correct")}</p>
          </div>
          <p className="text-base font-bold">
            {formatSeconds(correctnessTime.correct.average_time_seconds)}
          </p>
        </div>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <XCircle className="h-5 w-5 flex-shrink-0 text-red-500" />
            <p className="text-sm font-medium">{t("incorrect")}</p>
          </div>
          <p className="text-base font-bold">
            {formatSeconds(correctnessTime.incorrect.average_time_seconds)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
