"use client";

import React, { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EyeIcon } from "@heroicons/react/24/outline";
import { getDailyPointsSummary } from "@/services/gamification.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { useAuthCore } from "@/store/auth.store";
import Link from "next/link";
import { PATHS } from "@/constants/paths"; // Assuming you have a statistics path

interface DayData {
  name: string; // Day name (e.g., "الاحد")
  shortName: string; // e.g., "Sun" for mapping
  points: number;
  percent: number; // Calculated based on max points in the week
}

function Shapcontain({ showShapContain }: { showShapContain: boolean }) {
  const t = useTranslations("Nav.UserNav.ShapContain");
  const { isAuthenticated } = useAuthCore();
  // Get current locale for day names if needed, or handle in i18n
  // const locale = useLocale();

  const {
    data: weeklyPointsData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: [QUERY_KEYS.WEEKLY_POINTS_SUMMARY],
    queryFn: () => getDailyPointsSummary({ range: "week" }),
    enabled: showShapContain && isAuthenticated,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });

  const dayOrder = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const dayNames: { [key: string]: string } = {
    // Example for Arabic
    Sun: t("days.sun"),
    Mon: t("days.mon"),
    Tue: t("days.tue"),
    Wed: t("days.wed"),
    Thu: t("days.thu"),
    Fri: t("days.fri"),
    Sat: t("days.sat"),
  };

  const chartData: DayData[] = useMemo(() => {
    if (!weeklyPointsData?.results) {
      // Return default structure for skeletons or empty state
      return dayOrder.map((shortName) => ({
        name: dayNames[shortName] || shortName,
        shortName,
        points: 0,
        percent: 0,
      }));
    }

    const pointsByDay: Record<string, number> = {};
    weeklyPointsData.results.forEach((item) => {
      const dayOfWeek = new Date(item.date).toLocaleDateString("en-US", {
        weekday: "short",
      }); // 'Sun', 'Mon', etc.
      pointsByDay[dayOfWeek] =
        (pointsByDay[dayOfWeek] || 0) + item.total_points;
    });

    const maxPoints = Math.max(1, ...Object.values(pointsByDay), 10); // Ensure maxPoints is at least 1 or a sensible minimum for percentage calculation

    return dayOrder.map((shortName) => {
      const points = pointsByDay[shortName] || 0;
      return {
        name: dayNames[shortName] || shortName,
        shortName,
        points,
        percent: maxPoints > 0 ? (points / maxPoints) * 100 : 0,
      };
    });
  }, [weeklyPointsData, t]); // Add t to dependencies if dayNames are directly from t

  if (!showShapContain) {
    return null;
  }

  return (
    <div className="Shapcontain starcontain absolute top-[70px] z-50 w-72 rounded-2xl border bg-popover p-5 text-base text-popover-foreground shadow-lg transition-all duration-300 ltr:right-20 rtl:left-20 sm:left-auto sm:w-80">
      <p className="font-bold">{t("title")}</p>
      <p className="mt-1 text-sm text-muted-foreground">{t("description")}</p>

      <div className="mt-4 flex h-40 items-end justify-center gap-2 text-xs">
        {" "}
        {/* items-end for bars from bottom */}
        {isLoading &&
          Array.from({ length: 7 }).map((_, index) => (
            <div
              key={index}
              className="w-1/7 relative flex flex-col items-center text-center"
            >
              <Skeleton className="h-32 w-3 rounded-t-md bg-muted" />{" "}
              {/* Bar skeleton */}
              <Skeleton className="mt-1 h-3 w-6 bg-muted" />{" "}
              {/* Day name skeleton */}
            </div>
          ))}
        {!isLoading &&
          !isError &&
          chartData.map((day) => (
            <div
              key={day.shortName}
              className="w-1/7 relative flex flex-col items-center text-center"
            >
              <div
                className="flex h-full w-3 items-end rounded-t-md bg-muted"
                title={`${day.name}: ${day.points} ${t("pointsSuffix")}`}
              >
                <div
                  className="w-full rounded-t-md bg-primary transition-all duration-500 ease-out"
                  style={{ height: `${day.percent}%` }}
                ></div>
              </div>
              <div className="mt-1 text-[10px] text-muted-foreground">
                {day.name}
              </div>
            </div>
          ))}
        {isError && (
          <p className="col-span-7 text-center text-destructive">
            {t("errorLoading")}
          </p>
        )}
      </div>

      <div className="mt-5 flex justify-center">
        <Link href={`${PATHS.STUDY_HOME}/statistics`} passHref legacyBehavior>
          <Button
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <EyeIcon className="h-5 w-5" />
            {t("viewAllButton")}
          </Button>
        </Link>
      </div>
    </div>
  );
}

export default Shapcontain;
