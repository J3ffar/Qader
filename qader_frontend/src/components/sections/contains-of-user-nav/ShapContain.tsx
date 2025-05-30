"use client";

import React, { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EyeIcon } from "@heroicons/react/24/outline";
import { getDailyPointsSummary } from "@/services/gamification.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { useAuthCore } from "@/store/auth.store";
import Link from "next/link";
import { PATHS } from "@/constants/paths"; // Assuming you have a statistics path

interface DayData {
  name: string;
  shortName: string; // e.g., "Sun", "Mon"
  points: number;
  percent: number; // Calculated based on max points in the week, or a fixed goal
  isToday: boolean;
}

function Shapcontain({ showShapContain }: { showShapContain: boolean }) {
  const t = useTranslations("Nav.UserNav.ShapContain");
  const locale = useLocale();
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

  const { dayOrder, dayNames, todayShortName } = useMemo(() => {
    const now = new Date();
    // 'en-US' weekday: 'short' gives 'Sun', 'Mon', etc.
    const currentTodayShortName = now.toLocaleDateString("en-US", {
      weekday: "short",
    });

    // New order: Sunday to Saturday
    const order = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const names: { [key: string]: string } = {
      // Ensure these keys match your i18n file
      Sun: t("days.sun"),
      Mon: t("days.mon"),
      Tue: t("days.tue"),
      Wed: t("days.wed"),
      Thu: t("days.thu"),
      Fri: t("days.fri"),
      Sat: t("days.sat"),
    };
    return {
      dayOrder: order,
      dayNames: names,
      todayShortName: currentTodayShortName,
    };
  }, [t]);

  const chartData: DayData[] = useMemo(() => {
    const pointsByAPIDate: Record<string, number> = {};
    if (weeklyPointsData?.results) {
      weeklyPointsData.results.forEach((item) => {
        pointsByAPIDate[item.date] = item.total_points;
      });
    }

    const maxPointsInWeek = Math.max(
      10, // Set a minimum sensible value for maxPoints to scale against, e.g., 10 points
      ...(weeklyPointsData?.results?.map((item) => item.total_points) || [0])
    );

    const currentWeekDays = dayOrder.map((_, index) => {
      const date = new Date();
      const currentDayOfWeekJS = date.getDay();

      const diffToSunday = -currentDayOfWeekJS;

      date.setDate(date.getDate() + diffToSunday + index); // Add index to iterate through the week starting from Sunday
      return date.toISOString().split("T")[0];
    });

    return dayOrder.map((shortName, index) => {
      const dateForThisDay = currentWeekDays[index];
      const points = pointsByAPIDate[dateForThisDay] || 0;
      let percent = maxPointsInWeek > 0 ? (points / maxPointsInWeek) * 100 : 0;
      // Ensure percent is not above 100 if points somehow exceed a defined max (not the case here with relative scaling)
      percent = Math.min(percent, 100);

      return {
        name: dayNames[shortName] || shortName,
        shortName,
        points,
        percent, // This will be used for the main bar height
        isToday: shortName === todayShortName,
      };
    });
  }, [weeklyPointsData, dayOrder, dayNames, todayShortName]);

  if (!showShapContain) {
    return null;
  }

  const MIN_BAR_HEIGHT_PERCENTAGE = 3;
  return (
    <div className="Shapcontain starcontain absolute top-[70px] z-50 w-72 rounded-2xl border bg-popover p-5 text-base text-popover-foreground shadow-lg transition-all duration-300 ltr:right-20 rtl:left-20 sm:left-auto sm:w-80">
      <p className="font-bold">{t("title")}</p>
      <p className="mt-1 text-sm text-muted-foreground">{t("description")}</p>

      {!isLoading && !isError && chartData.every((d) => d.points === 0) && (
        <p className="col-span-7 py-1 text-right text-sm text-muted-foreground">
          {t("noActivity")}
        </p>
      )}
      <div className="mt-4 flex h-40 items-end justify-center gap-2 text-xs">
        {isLoading &&
          Array.from({ length: 7 }).map((_, index) => (
            <div
              key={index}
              className="w-1/7 relative flex flex-1 flex-col items-center text-center"
            >
              <Skeleton className="h-32 w-3 rounded-t-md bg-muted" />
              <Skeleton className="mt-1 h-3 w-full max-w-[30px] bg-muted" />
            </div>
          ))}
        {!isLoading &&
          !isError &&
          chartData.map((day) => (
            <div
              key={day.shortName}
              className={`relative text-center flex flex-col items-center w-1/7 flex-1 ${
                day.isToday ? "font-semibold" : ""
              }`}
            >
              <div
                className="h-35 flex w-3 items-end rounded-t-md bg-muted" // Bar container
                title={`${day.name}: ${day.points} ${t("pointsSuffix")}`}
              >
                <div
                  className={`w-full ${
                    day.isToday ? "bg-primary" : "bg-accent"
                  } rounded-t-md transition-all duration-500 ease-out`} // Bar itself
                  style={{
                    height: `${Math.max(
                      day.percent,
                      MIN_BAR_HEIGHT_PERCENTAGE
                    )}%`,
                  }} // APPLY MINIMUM HEIGHT
                ></div>
              </div>
              <div
                className={`mt-1 text-[10px] ${
                  day.isToday
                    ? "text-accent-foreground font-bold"
                    : "text-muted-foreground"
                }`}
              >
                {day.name}
              </div>
            </div>
          ))}
        {isError && (
          <p className="col-span-7 py-10 text-center text-destructive">
            {t("errorLoading")}
          </p>
        )}
      </div>

      <div className="mt-5 flex justify-center">
        <Link
          href={`/${locale}${PATHS.STUDY.HOME}/statistics`}
          passHref
          legacyBehavior
        >
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
