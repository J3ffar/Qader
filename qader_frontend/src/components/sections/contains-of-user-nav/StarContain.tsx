"use client";

import React, { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StarIcon as HeroStarIcon, EyeIcon } from "@heroicons/react/24/outline"; // Renamed
import { Progress } from "@/components/ui/progress"; // For progress bar
import { getStudyDaysLog } from "@/services/gamification.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { useAuthCore } from "@/store/auth.store";
import Link from "next/link";
import { PATHS } from "@/constants/paths";

interface DayStreakInfo {
  name: string;
  shortName: string;
  active: boolean;
}

const StarContain = ({ showStarContainer }: { showStarContainer: boolean }) => {
  const t = useTranslations("Nav.UserNav.StarContain");
  const { user, isAuthenticated } = useAuthCore();
  const currentStreak = user?.current_streak_days ?? 0;
  const streakGoal = 5; // Example goal, could be dynamic later

  // Get current date to determine the current week range
  const today = new Date();
  const firstDayOfWeek = new Date(today);
  firstDayOfWeek.setDate(
    today.getDate() - today.getDay() + (today.getDay() === 0 ? -6 : 1)
  ); // Assuming week starts on Monday (adjust if Sunday)
  const lastDayOfWeek = new Date(firstDayOfWeek);
  lastDayOfWeek.setDate(firstDayOfWeek.getDate() + 6);

  const formatDateForAPI = (date: Date) => date.toISOString().split("T")[0];

  const {
    data: studyDaysData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: [
      QUERY_KEYS.STUDY_DAYS_LOG,
      formatDateForAPI(firstDayOfWeek),
      formatDateForAPI(lastDayOfWeek),
    ],
    queryFn: () =>
      getStudyDaysLog({
        date_range_after: formatDateForAPI(firstDayOfWeek),
        date_range_before: formatDateForAPI(lastDayOfWeek),
      }),
    enabled: showStarContainer && isAuthenticated,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });

  const dayOrder = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]; // Assuming Monday start
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

  const weeklyStreakData: DayStreakInfo[] = useMemo(() => {
    const activeDays = new Set(
      studyDaysData?.results.map((log) => {
        const date = new Date(log.study_date + "T00:00:00"); // Ensure date is parsed correctly
        return date.toLocaleDateString("en-US", { weekday: "short" });
      })
    );

    return dayOrder.map((shortName) => ({
      name: dayNames[shortName] || shortName,
      shortName,
      active: activeDays.has(shortName),
    }));
  }, [studyDaysData, t]); // Add t if dayNames are directly from t

  if (!showStarContainer) {
    return null;
  }

  return (
    <div className="starcontain absolute top-[70px] z-50 w-72 rounded-2xl border bg-popover p-5 text-base text-popover-foreground shadow-lg transition-all duration-300 ltr:right-8 rtl:left-8 sm:left-auto sm:w-80 ltr:sm:right-40 rtl:sm:left-40">
      <p className="font-bold">{t("title")}</p>
      <p className="mt-1 text-sm text-muted-foreground">{t("description")}</p>

      <div className="mt-4 flex items-center">
        <HeroStarIcon className="mr-3 h-10 w-10 flex-shrink-0 text-yellow-500" />
        <div className="flex-1">
          {isLoading && !user ? (
            <Skeleton className="mb-1 h-5 w-3/4" />
          ) : (
            <p>{t("streakDays", { count: currentStreak })}</p>
          )}
          <div className="mt-1 flex items-center gap-2">
            {isLoading && !user ? (
              <Skeleton className="h-2 w-14" />
            ) : (
              <Progress
                value={(currentStreak / streakGoal) * 100}
                className="h-2 w-14"
              />
            )}
            <span className="text-xs text-muted-foreground">
              {currentStreak}/{streakGoal}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-4 gap-x-2 gap-y-1 text-xs">
        {" "}
        {/* Adjusted for better layout */}
        {isLoading &&
          Array.from({ length: 7 }).map((_, index) => (
            <div key={index} className="flex items-center">
              <Skeleton className="mr-1 h-5 w-5 rounded-full" />
              <Skeleton className="h-3 w-8" />
            </div>
          ))}
        {!isLoading &&
          !isError &&
          weeklyStreakData.map((day) => (
            <div key={day.shortName} className="flex items-center">
              <HeroStarIcon
                className={`w-5 h-5 mr-1 ${
                  day.active ? "text-yellow-500" : "text-muted-foreground/50"
                }`}
              />
              <span
                className={day.active ? "font-medium" : "text-muted-foreground"}
              >
                {day.name}
              </span>
            </div>
          ))}
        {isError && (
          <p className="col-span-full text-center text-destructive">
            {t("errorLoading")}
          </p>
        )}
      </div>

      <div className="mt-5 flex justify-center">
        <Link href={`${PATHS.STUDY_HOME}/statistics`} passHref legacyBehavior>
          {/* Or a dedicated streak page */}
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
};

export default StarContain;
