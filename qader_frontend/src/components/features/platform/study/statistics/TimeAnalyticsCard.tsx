"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { CheckCircle2, Clock, XCircle, Timer } from "lucide-react";
import { useTranslations } from "next-intl";
import type { UserStatistics } from "@/types/api/study.types";
import { Separator } from "@/components/ui/separator";

interface Props {
  timeAnalytics: UserStatistics["time_analytics"];
}

const formatSeconds = (seconds: number | null, fallback = "N/A"): string => {
  if (seconds === null || seconds === undefined) return fallback;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
};

export function TimeAnalyticsCard({ timeAnalytics }: Props) {
  const t = useTranslations("Study.statistics.timeAnalytics");
  const tCommon = useTranslations("Common");

  const {
    average_time_per_question_by_correctness: correctnessTime,
    overall_average_time_per_question_seconds: overallAvg,
    average_test_duration_by_type: durationByType,
  } = timeAnalytics;

  const durationEntries = Object.values(durationByType);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-start justify-between gap-4 rounded-lg bg-muted/50 p-3">
          <div className="flex items-center gap-3">
            <Timer className="h-5 w-5 flex-shrink-0 text-muted-foreground" />
            <p className="text-sm font-medium">{t("overallAverage")}</p>
          </div>
          <p className="text-base font-bold">{formatSeconds(overallAvg)}</p>
        </div>
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
      {durationEntries.length > 0 && (
        <>
          <Separator />
          <CardFooter className="flex-col items-start gap-3 pt-4">
            <h4 className="text-sm font-semibold">
              {t("averageDurationByTypeTitle")}
            </h4>
            <div className="w-full space-y-2 text-sm">
              {durationEntries.map((entry) => (
                <div
                  key={entry.attempt_type_value}
                  className="flex justify-between"
                >
                  <p className="text-muted-foreground">
                    {tCommon(`testTypes.${entry.attempt_type_value}`)}
                  </p>
                  <p className="font-medium">
                    {formatSeconds(entry.average_duration_seconds)}
                  </p>
                </div>
              ))}
            </div>
          </CardFooter>
        </>
      )}
    </Card>
  );
}
