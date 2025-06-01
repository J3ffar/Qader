"use client";

import React, { useMemo, forwardRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { EyeIcon } from "@heroicons/react/24/outline"; // Or Lucide equivalent: Eye
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getDailyPointsSummary } from "@/services/gamification.service"; // Adjust path
import { QUERY_KEYS } from "@/constants/queryKeys"; // Adjust path
import { useAuthCore } from "@/store/auth.store"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path

interface DayData {
  name: string;
  shortName: string;
  points: number;
  percent: number;
  isToday: boolean;
}

interface PointsSummaryDropdownProps {
  isVisible: boolean;
}

const PointsSummaryDropdown = forwardRef<
  HTMLDivElement,
  PointsSummaryDropdownProps
>(({ isVisible }, ref) => {
  const t = useTranslations("Nav.PlatformHeader.PointsSummaryDropdown"); // Ensure i18n keys are suitable
  const locale = useLocale();
  const { isAuthenticated } = useAuthCore();

  const {
    data: weeklyPointsData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: [QUERY_KEYS.WEEKLY_POINTS_SUMMARY],
    queryFn: () => getDailyPointsSummary({ range: "week" }),
    enabled: isVisible && isAuthenticated,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });

  const { dayOrder, dayNames, todayShortName } = useMemo(() => {
    const now = new Date();
    const currentTodayShortName = now.toLocaleDateString("en-US", {
      // Keep en-US for consistency in shortName keys
      weekday: "short",
    });
    const order = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const names: { [key: string]: string } = {
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
      10,
      ...(weeklyPointsData?.results?.map((item) => item.total_points) || [0])
    );
    const currentWeekDays = dayOrder.map((_, index) => {
      const date = new Date();
      const currentDayOfWeekJS = date.getDay(); // Sunday = 0, Saturday = 6
      const diffToSunday = -currentDayOfWeekJS;
      date.setDate(date.getDate() + diffToSunday + index);
      return date.toISOString().split("T")[0];
    });

    return dayOrder.map((shortName, index) => {
      const dateForThisDay = currentWeekDays[index];
      const points = pointsByAPIDate[dateForThisDay] || 0;
      let percent = maxPointsInWeek > 0 ? (points / maxPointsInWeek) * 100 : 0;
      percent = Math.min(percent, 100);
      return {
        name: dayNames[shortName] || shortName,
        shortName,
        points,
        percent,
        isToday: shortName === todayShortName,
      };
    });
  }, [weeklyPointsData, dayOrder, dayNames, todayShortName]);

  if (!isVisible) {
    return null;
  }

  const MIN_BAR_HEIGHT_PERCENTAGE = 3;

  // Positioning: Assuming points icon is to the right of streak icon
  // Adjust ltr:right-X and rtl:left-X as needed.
  const positionClasses =
    "ltr:right-20 rtl:left-20 md:ltr:right-28 md:rtl:left-28";

  return (
    <div
      ref={ref}
      className={`absolute top-[calc(100%+8px)] z-50 w-72 rounded-2xl border bg-popover p-5 text-base text-popover-foreground shadow-lg transition-all duration-300 sm:w-80 ${positionClasses}`}
    >
      <p className="font-bold">{t("title")}</p>
      <p className="mt-1 text-sm text-muted-foreground">{t("description")}</p>

      {!isLoading && !isError && chartData.every((d) => d.points === 0) && (
        <p className="py-1 text-center text-sm text-muted-foreground">
          {" "}
          {/* Adjusted for centering */}
          {t("noActivity")}
        </p>
      )}
      <div className="mt-4 flex h-40 items-end justify-center gap-2 text-xs">
        {isLoading &&
          Array.from({ length: 7 }).map((_, index) => (
            <div
              key={index}
              className="relative flex flex-1 flex-col items-center text-center"
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
              className={`relative flex w-1/7 flex-1 flex-col items-center text-center ${
                day.isToday ? "font-semibold" : ""
              }`}
            >
              <div
                className="h-35 flex w-3 items-end rounded-t-md bg-muted" // Bar container, ensure h-full or specific height
                title={`${day.name}: ${day.points} ${t("pointsSuffix")}`}
              >
                <div
                  className={`w-full rounded-t-md bg-primary transition-all duration-500 ease-out`}
                  style={{
                    height: `${Math.max(
                      day.percent,
                      MIN_BAR_HEIGHT_PERCENTAGE
                    )}%`,
                  }}
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
        <Button
          asChild
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <Link href={`/${locale}${PATHS.STUDY.HOME}/statistics`}>
            <EyeIcon className="h-5 w-5" />
            {t("viewAllButton")}
          </Link>
        </Button>
      </div>
    </div>
  );
});

PointsSummaryDropdown.displayName = "PointsSummaryDropdown";
export default PointsSummaryDropdown;
