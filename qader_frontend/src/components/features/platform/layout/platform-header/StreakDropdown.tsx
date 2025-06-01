"use client";

import React, { useMemo, forwardRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { StarIcon as HeroStarIcon, EyeIcon } from "@heroicons/react/24/outline"; // Or Lucide: Star, Eye
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { getStudyDaysLog } from "@/services/gamification.service"; // Adjust path
import { QUERY_KEYS } from "@/constants/queryKeys"; // Adjust path
import { useAuthCore } from "@/store/auth.store"; // Adjust path
import { PATHS } from "@/constants/paths"; // Adjust path

interface DayStreakInfo {
  name: string;
  shortName: string;
  active: boolean;
}

interface StreakDropdownProps {
  isVisible: boolean;
}

const StreakDropdown = forwardRef<HTMLDivElement, StreakDropdownProps>(
  ({ isVisible }, ref) => {
    const t = useTranslations("Nav.PlatformHeader.StreakDropdown"); // Ensure i18n keys
    const locale = useLocale();
    const { user, isAuthenticated } = useAuthCore();
    const currentStreak = user?.current_streak_days ?? 0;
    const streakGoal = 5; // Example, make configurable if needed

    const today = new Date();
    const firstDayOfWeek = new Date(today);
    // Assuming week starts on Monday for display. API might handle week definitions differently.
    const dayOfWeek = today.getDay(); // Sunday = 0, Monday = 1, ..., Saturday = 6
    const offset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Adjust to Monday
    firstDayOfWeek.setDate(today.getDate() + offset);

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
      enabled: isVisible && isAuthenticated,
      staleTime: 1000 * 60 * 10,
    });

    // Weekday order for display (e.g., Mon-Sun or Sun-Sat) - match your locale's typical week start
    // This example uses Mon-Sun. Adjust `dayOrder` and `dayNames` keys accordingly.
    const { dayOrder, dayNames } = useMemo(() => {
      // Let's define order as Sun-Sat to match typical calendar views
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
      return { dayOrder: order, dayNames: names };
    }, [t]);

    const weeklyStreakData: DayStreakInfo[] = useMemo(() => {
      const activeDays = new Set(
        studyDaysData?.results.map((log) => {
          const date = new Date(log.study_date + "T00:00:00Z"); // Ensure UTC context if API date is timezone-naive
          return date.toLocaleDateString("en-US", {
            weekday: "short",
            timeZone: "UTC",
          });
        })
      );
      return dayOrder.map((shortName) => ({
        name: dayNames[shortName] || shortName,
        shortName,
        active: activeDays.has(shortName),
      }));
    }, [studyDaysData, dayOrder, dayNames]);

    if (!isVisible) {
      return null;
    }

    // Positioning: Assuming streak icon is one of the leftmost.
    // Adjust ltr:right-X and rtl:left-X as needed.
    const positionClasses =
      "ltr:right-40 rtl:left-40 md:ltr:right-56 md:rtl:left-56";

    return (
      <div
        ref={ref}
        className={`absolute top-[calc(100%+8px)] z-50 w-72 rounded-2xl border bg-popover p-5 text-base text-popover-foreground shadow-lg transition-all duration-300 sm:w-80 ${positionClasses}`}
      >
        <p className="font-bold">{t("title")}</p>
        <p className="mt-1 text-sm text-muted-foreground">{t("description")}</p>

        <div className="mt-4 flex items-center">
          <HeroStarIcon className="mr-3 h-10 w-10 flex-shrink-0 text-yellow-500 rtl:ml-3 rtl:mr-0" />
          <div className="flex-1">
            {isLoading && !user && isAuthenticated ? ( // Show skeleton if loading and user data not yet available but authenticated
              <Skeleton className="mb-1 h-5 w-3/4" />
            ) : (
              <p>{t("streakDays", { count: currentStreak })}</p>
            )}
            <div className="mt-1 flex items-center gap-2">
              {isLoading && !user && isAuthenticated ? (
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
          {isLoading &&
            Array.from({ length: 7 }).map((_, index) => (
              <div key={index} className="flex items-center">
                <Skeleton className="mr-1 h-5 w-5 rounded-full rtl:ml-1 rtl:mr-0" />
                <Skeleton className="h-3 w-8" />
              </div>
            ))}
          {!isLoading &&
            !isError &&
            weeklyStreakData.map((day) => (
              <div key={day.shortName} className="flex items-center">
                <HeroStarIcon
                  className={`h-5 w-5 mr-1 rtl:ml-1 rtl:mr-0 ${
                    day.active ? "text-yellow-500" : "text-muted-foreground/50"
                  }`}
                />
                <span
                  className={
                    day.active ? "font-medium" : "text-muted-foreground"
                  }
                >
                  {day.name}
                </span>
              </div>
            ))}
          {isError && (
            <p className="col-span-full py-5 text-center text-destructive">
              {" "}
              {/* Added padding for better display */}
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
  }
);

StreakDropdown.displayName = "StreakDropdown";
export default StreakDropdown;
