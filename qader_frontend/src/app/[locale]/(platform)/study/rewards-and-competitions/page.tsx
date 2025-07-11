"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  fetchPointsTotal,
  getAllBadges,
  getGamificationSummary,
  getMyPurchasedItems,
  getPointsSummary,
  getRewardStoreItems,
  getStudyDaysLog,
  purchaseRewardItem,
} from "@/services/gamification.service";
import {
  Badge,
  GamificationSummary,
  PaginatedDailyPointSummaryResponse,
  PaginatedStudyDayLogResponse,
  PointsDataType,
  PointsSummary,
  PurchasedItemResponse,
  RewardStoreItem,
  StoreItemGamificaiton,
} from "@/types/api/gamification.types";
import { ChevronDownIcon } from "@heroicons/react/24/outline";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { format, parseISO, subDays } from "date-fns";
import dayjs from "dayjs";
import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

const RewardsDashboard = () => {
  const todayIndex = new Date().getDay();
  // start the madaka?

  const today = dayjs().format("YYYY-MM-DD");
  const weekStart = dayjs().startOf("week").format("YYYY-MM-DD");
  const weekEnd = dayjs().endOf("week").format("YYYY-MM-DD");
  const monthStart = dayjs()
    .subtract(1, "month")
    .startOf("month")
    .format("YYYY-MM-DD");
  const lastWeekStart = dayjs()
    .subtract(1, "week")
    .startOf("week")
    .format("YYYY-MM-DD");
  const lastWeekEnd = dayjs()
    .subtract(1, "week")
    .endOf("week")
    .format("YYYY-MM-DD");

  const monthEnd = dayjs()
    .subtract(1, "month")
    .endOf("month")
    .format("YYYY-MM-DD");
  const last90Days = dayjs().subtract(90, "day").format("YYYY-MM-DD");

  const usePointsTotals = () => {
    const todayQuery = useQuery({
      queryKey: ["points-total", "today"],
      queryFn: () => fetchPointsTotal(today, today),
      refetchOnWindowFocus: true,
    });

    const thisWeekQuery = useQuery({
      queryKey: ["points-total", "this-week"],
      queryFn: () => fetchPointsTotal(weekStart, weekEnd),
      refetchOnWindowFocus: true,
    });
    const lastWeekQuery = useQuery({
      queryKey: ["points-total", "last-week"],
      queryFn: () => fetchPointsTotal(lastWeekStart, lastWeekEnd),
      refetchOnWindowFocus: true,
    });
    const lastMonthQuery = useQuery({
      queryKey: ["points-total", "last-month"],
      queryFn: () => fetchPointsTotal(monthStart, monthEnd),
      refetchOnWindowFocus: true,
    });

    const last90DaysQuery = useQuery({
      queryKey: ["points-total", "last-90-days"],
      queryFn: () => fetchPointsTotal(last90Days, today),
      refetchOnWindowFocus: true,
    });
    return {
      todayTotal: todayQuery.data ?? 0,
      thisWeekTotal: thisWeekQuery.data ?? 0,
      lastWeekQuery: lastWeekQuery.data ?? 0,
      lastMonthTotal: lastMonthQuery.data ?? 0,
      last90DaysTotal: last90DaysQuery.data ?? 0,
      isLoading:
        todayQuery.isLoading ||
        thisWeekQuery.isLoading ||
        lastMonthQuery.isLoading ||
        last90DaysQuery.isLoading,
    };
  };
  const {
    todayTotal,
    thisWeekTotal,
    lastMonthTotal,
    last90DaysTotal,
    lastWeekQuery,
    isLoading: isLoadingPointsTotal,
  } = usePointsTotals();

  // end the madaka
  const defaultStoreItems: StoreItemGamificaiton[] = [
    {
      id: 0,
      title: "تصاميم",
      desc: "استبدل 20 نقطة مقابل الحصول على تصاميم، شرح وافٍ لما ستحصل عليه.",
      points: 20,
      image_url: "",
    },
    {
      id: 1,
      title: "الدخول للمسابقة الكبرى",
      desc: "استبدل 30 نقطة مقابل الدخول للمسابقة الكبرى، التي سيتم الإعلان عنها لاحقاً.",
      points: 30,
      image_url: "",
    },
    {
      id: 2,
      title: "أشعار",
      desc: "استبدل 10 نقاط مقابل الحصول على أشعار، شرح وافٍ لما ستحصل عليه.",
      points: 10,
      image_url: "",
    },
    {
      id: 3,
      title: "مخطوطة",
      desc: "استبدل 5 نقاط مقابل الحصول على مخطوطة، شرح وافٍ لما ستحصل عليه.",
      points: 5,
      image_url: "",
    },
  ];

  const [showConfirm, setShowConfirm] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [selectedReward, setSelectedReward] = useState<{
    id: number | string;
    title: string;
    points: number;
  } | null>(null);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [selectedRangeDailyPoints, setSelectedRangeDailyPoints] =
    useState("هذا الأسبوع");
  const [selectedRangeTestPoints, setSelectedRangeTestPoints] =
    useState("هذا الأسبوع");

  const [selectedRangeBadgRanges, setSelectedRangeBadgRanges] =
    useState("خاصتي");

  const BadgRanges = ["الكل", "خاصتي"];
  const ranges = [
    "هذا الأسبوع",
    "الأسبوع الماضي",
    "نقاط اليوم",
    "الشهر الماضي",
    "آخر 90 يوم",
  ];
  const handleSelectDailyPoints = (range: string) => {
    setSelectedRangeDailyPoints(range);
  };
  const handleSelectTestPoints = (range: string) => {
    setSelectedRangeTestPoints(range);
  };
  const handleSelectBadgRanges = (BadgRanges: string) => {
    setSelectedRangeBadgRanges(BadgRanges);
  };
  const { data: summaryData, isLoading: isLoadingSummary } =
    useQuery<GamificationSummary>({
      queryKey: ["gamificationSummary"],
      queryFn: getGamificationSummary,
    });
  // start days summary
  const { data: PointsSummary, isLoading: isLoadingPointsSummary } =
    useQuery<PaginatedDailyPointSummaryResponse>({
      queryKey: ["mPointsSummary"],
      queryFn: getPointsSummary,
    });
  type PointsData = { day: string; percent: number };

  const daysMap: Record<number, string> = {
    0: "الأحد",
    1: "الإثنين",
    2: "الثلاثاء",
    3: "الأربعاء",
    4: "الخميس",
    5: "الجمعة",
    6: "السبت",
  };

  const results = PointsSummary?.results ?? [];

  const weekStartDate = dayjs().startOf("week");
  const weekEndDate = dayjs().endOf("week");

  const currentWeekResults = results.filter(({ date }) => {
    const day = dayjs(date);
    return (
      day.isAfter(weekStartDate.subtract(1, "day")) &&
      day.isBefore(weekEndDate.add(1, "day"))
    );
  });

  const dayPointsMap: Record<string, number> = {};
  currentWeekResults.forEach(({ date, total_points }) => {
    const dayIndex = new Date(date).getDay();
    const dayName = daysMap[dayIndex];
    dayPointsMap[dayName] = total_points;
  });

  const fullWeek: PointsDataType[] = Object.values(daysMap).map((day) => ({
    day,
    percent: dayPointsMap[day] ?? 0,
  }));
  const [activeIndexes, setActiveIndexes] = useState<number[]>([]);
  const mylastWeekStart = useMemo(
    () => dayjs().subtract(1, "week").startOf("week"),
    []
  );
  const mylastWeekEnd = useMemo(
    () => dayjs().subtract(1, "week").endOf("week"),
    []
  );
  const [myLastWeekData, setMyLastWeekData] = useState<PointsDataType[]>();
  useEffect(() => {
    if (fullWeek && fullWeek.length > 0) {
      const indexes = fullWeek
        .map((item, index) => (item.percent > 0 ? index : null))
        .filter((i): i is number => i !== null);

      const areEqual =
        indexes.length === activeIndexes.length &&
        indexes.every((val, i) => val === activeIndexes[i]);

      if (!areEqual) {
        setActiveIndexes(indexes);
      }
    }
  }, [activeIndexes, fullWeek]);
  //last week charts
  useEffect(() => {
    const lastWeekResults = results.filter(({ date }) => {
      const day = dayjs(date);
      return (
        day.isAfter(mylastWeekStart.subtract(1, "day")) &&
        day.isBefore(mylastWeekEnd.add(1, "day"))
      );
    });

    const lastWeekDayPointsMap: Record<string, number> = {};

    lastWeekResults.forEach(({ date, total_points }) => {
      const dayIndex = new Date(date).getDay();
      const dayName = daysMap[dayIndex];
      lastWeekDayPointsMap[dayName] = total_points;
    });

    const aLastWeekData: PointsDataType[] = Object.values(daysMap).map(
      (day) => ({
        day,
        percent: lastWeekDayPointsMap[day] ?? 0,
      })
    );

    setMyLastWeekData(aLastWeekData);
  }, [results, mylastWeekStart, mylastWeekEnd]);

  // end of  days summary
  const [testPoints] = useState(fullWeek);

  const { data: badgesData, isLoading: isLoadingBadges } = useQuery<Badge[]>({
    queryKey: ["myBadges"],
    queryFn: getAllBadges,
  });
  const { data: studyDaysData, isLoading: isLoadingStudyDays } =
    useQuery<PaginatedStudyDayLogResponse>({
      queryKey: ["StudyDaysLog"],
      queryFn: () => getStudyDaysLog(),
      refetchOnWindowFocus: true,
    });

  const [myStreak, setMyStreak] = useState(0);

  useEffect(() => {
    if (
      !studyDaysData ||
      !studyDaysData.results ||
      !Array.isArray(studyDaysData.results)
    ) {
      return;
    }

    const studyDates = studyDaysData.results.map((item) => item.study_date);

    const dateSet = new Set(
      studyDates.map((date) => format(parseISO(date), "yyyy-MM-dd"))
    );

    const mtoday = new Date();
    const todayStr = format(mtoday, "yyyy-MM-dd");

    let startIndex = 0;
    if (!dateSet.has(todayStr)) {
      startIndex = 1;
    }

    let count = 0;
    for (let i = startIndex; i < 100; i++) {
      const checkDate = format(subDays(mtoday, i), "yyyy-MM-dd");
      if (dateSet.has(checkDate)) {
        count++;
      } else {
        break;
      }
    }

    setMyStreak(count);
  }, [studyDaysData]);
  //end the try

  const { data: pointsData } = useQuery<PointsSummary>({
    queryKey: ["pointsSummary"],
    queryFn: getPointsSummary,
  });

  const { data: PurchasedItems, refetch: refetchPurchasedItems } =
    useQuery<PurchasedItemResponse>({
      queryKey: ["getMyPurchasedItems"],
      queryFn: getMyPurchasedItems,
    });
  const PurchasedItemsIds =
    PurchasedItems?.results.map((entry) => entry.item.id) ?? [];
  const { data: storeData, isLoading: isLoadingStore } = useQuery<
    RewardStoreItem[]
  >({
    queryKey: ["rewardStoreItems"],
    queryFn: getRewardStoreItems,
  });
  const queryClient = useQueryClient();

  // Derived state
  const mybadgesCount = badgesData?.filter((b) => b.is_earned).length || 0;
  const badgesCount = badgesData?.length || 0;
  const myBadges = badgesData || [];
  const streakPoints = (summaryData?.current_streak || 0) * 10;
  const pointsSummary = pointsData?.points || 0;
  const activeDays = Array.from(
    { length: 7 },
    (_, i) => i < (summaryData?.current_streak || 0)
  );
  const storeItems =
    storeData && storeData.length > 0
      ? storeData.map((item) => ({
          id: item.id,
          title: item.name,
          desc: item.description,
          points: item.cost_points,
          image_url: item.image_url,
        }))
      : defaultStoreItems;

  // Handle reward purchase
  const handlePurchase = async () => {
    if (!selectedReward) return;

    setIsPurchasing(true);
    try {
      await purchaseRewardItem(selectedReward.id);
      setIsConfirmed(true);
      queryClient.invalidateQueries({ queryKey: ["getMyPurchasedItems"] });
      queryClient.invalidateQueries({ queryKey: ["pointsSummary"] });
      queryClient.invalidateQueries({ queryKey: ["gamificationSummary"] });
      await refetchPurchasedItems();
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("حدث خطأ غير متوقع");
      }

      setShowConfirm(false);
    } finally {
      setIsPurchasing(false);
    }
  };
  const testingChartData =
    selectedRangeTestPoints === "الأسبوع الماضي"
      ? myLastWeekData || fullWeek
      : selectedRangeTestPoints === "نقاط اليوم"
      ? fullWeek.filter((_, index) => index === todayIndex)
      : fullWeek;

  return (
    <div className="py-5 sm:p-5 space-y-6 dark:bg-[#081028]">
      <h1 className="text-4xl pr-3 font-bold leading-9">
        مكافآت المذاكرة والمسابقات
      </h1>
      <div className="flex flex-wrap gap-6 justify-center">
        {/* Achievement and Weekly Stars Section */}
        <div className="min-w-[300px] space-y-6 font-sans text-right">
          {/* Badges Card */}
          <div className="rounded-[20px] border border-[#E0E0E0] bg-white dark:bg-[#0B1739] px-5 py-6 shadow-sm space-y-5 max-w-[400px]">
            {isLoadingBadges ? (
              <>
                {/* Badges Skeleton */}
                <div className="flex items-center justify-between overflow-hidden">
                  <div className="h-5 w-1/4 bg-gray-200 rounded-full animate-pulse"></div>
                  <div className="h-8 w-20 bg-gray-200 rounded-md animate-pulse"></div>
                </div>

                <div className="text-center space-y-3 overflow-hidden">
                  <div className="h-12 w-24 mx-auto bg-gray-200 rounded-xl animate-pulse"></div>
                  <div className="h-4 w-1/3 mx-auto bg-gray-200 rounded-full animate-pulse"></div>
                </div>

                <div className="flex flex-wrap justify-center gap-4 overflow-hidden">
                  {[...Array(9)].map((_, i) => (
                    <div
                      key={i}
                      className="w-10 h-10 rounded-full bg-gray-200 animate-pulse"
                    ></div>
                  ))}
                </div>
              </>
            ) : (
              <>
                {/* Header */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span className="font-bold dark:text-[#FDFDFD]">
                    شارات الإنجاز
                  </span>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <div className="flex min-w-fit text-gray-500 gap-2 items-center cursor-pointer">
                        <span>{selectedRangeBadgRanges}</span>
                        <ChevronDownIcon className="size-4" />
                      </div>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {BadgRanges.map((range) => (
                        <DropdownMenuItem
                          key={range}
                          onClick={() => handleSelectBadgRanges(range)}
                        >
                          {range}
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Count */}
                <div className="text-center space-y-1">
                  <p className="text-[32px] font-extrabold text-[#003366] dark:text-[#3D93F5] leading-tight">
                    {selectedRangeBadgRanges == "الكل"
                      ? badgesCount
                      : mybadgesCount}
                  </p>
                  <p className="text-sm text-gray-500">شارة إنجاز</p>
                </div>

                {/* Emoji icons */}
                <div className="flex justify-center gap-2 text-[24px] leading-none flex-wrap ">
                  {["🥇", "🥈", "🏆", "🌟", "🎗️", "🌞", "🎯", "🏅", "👑"].map(
                    (emoji, index) => {
                      const badge = myBadges[index];

                      const isEarned =
                        selectedRangeBadgRanges == "الكل"
                          ? true
                          : badge?.is_earned === true;
                      const description =
                        badge?.description ??
                        "لم يتم الحصول على هذه الشارة بعد";

                      return (
                        <span
                          key={index}
                          title={description}
                          className={`${
                            isEarned ? "" : "grayscale opacity-50"
                          } transition duration-200 cursor-default`}
                        >
                          {badge?.icon_url ? (
                            <Image
                              alt=""
                              width={32}
                              height={32}
                              src={badge.icon_url}
                            />
                          ) : (
                            emoji
                          )}
                        </span>
                      );
                    }
                  )}
                </div>
              </>
            )}
          </div>

          {/* Streak Card */}
          <div className="rounded-[20px] border border-[#E0E0E0] bg-white dark:bg-[#0B1739] px-5 py-6 shadow-sm space-y-5 max-w-[400px]">
            {isLoadingStudyDays || isLoadingSummary ? (
              <>
                {/* Streak Skeleton */}
                <div className="h-5 w-1/3 bg-gray-200 rounded-full animate-pulse"></div>

                <div className="text-center space-y-3">
                  <div className="h-12 w-24 mx-auto bg-gray-200 rounded-xl animate-pulse"></div>
                  <div className="h-4 w-1/4 mx-auto bg-gray-200 rounded-full animate-pulse"></div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gray-200 animate-pulse"></div>
                  <div className="h-5 w-1/3 bg-gray-200 rounded-full animate-pulse"></div>
                </div>

                <div className="flex items-center gap-2 mt-1 pr-12">
                  <div className="flex-1 h-2 bg-gray-300 rounded-full overflow-hidden">
                    <div className="h-full bg-gray-200 animate-pulse w-3/4"></div>
                  </div>
                  <div className="h-4 w-10 bg-gray-200 rounded-full animate-pulse"></div>
                </div>

                <div className="flex gap-3 mt-4 text-xs text-center overflow-hidden">
                  {[...Array(7)].map((_, i) => (
                    <div
                      key={i}
                      className="flex flex-col items-center space-y-2"
                    >
                      <div className="w-6 h-6 rounded-full bg-gray-200 animate-pulse"></div>
                      <div className="h-3 w-12 bg-gray-200 rounded-full animate-pulse"></div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
                {/* Header */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span className="font-bold dark:text-[#FDFDFD]">
                    نقاط الأيام التالية
                  </span>
                </div>

                {/* Count */}
                <div className="text-center space-y-1">
                  <p className="text-[32px] font-extrabold text-[#003366] dark:text-[#3D93F5] leading-tight">
                    {streakPoints}
                  </p>
                  <p className="text-sm text-gray-500">نقطة</p>
                </div>

                {/* Streak line with icon */}
                <div className="flex gap-3 items-center font-medium text-[#2f80ed] mt-2 mb-0">
                  <Image
                    src="/images/rewards/flow-star.svg"
                    width={50}
                    height={50}
                    alt="star"
                    className="dark:invert-100"
                  />

                  <span className="text-sm text-black font-bold dark:text-[#FDFDFD]">
                    {myStreak || 0} أيام متتالية
                  </span>
                </div>

                {/* Progress */}
                <div className="flex items-center gap-2 mt-1 pr-12">
                  <div className="w-full max-w-[200px] h-2 bg-gray-300 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#2f80ed]"
                      style={{
                        width: `${Math.min(100, ((myStreak ?? 0) / 7) * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-600">
                    {myStreak || 0}/7
                  </span>
                </div>

                {/* Days */}
                <div className="flex gap-3 mt-4 text-xs text-center">
                  {[
                    "الأحد",
                    "الإثنين",
                    "الثلاثاء",
                    "الأربعاء",
                    "الخميس",
                    "الجمعة",
                    "السبت",
                  ].map((day, idx) => (
                    <div
                      key={idx}
                      className="flex flex-col items-center justify-center space-y-1"
                    >
                      {activeIndexes.includes(idx) &&
                      fullWeek[idx]?.percent > 0 ? (
                        <Image
                          width={20}
                          className="rotate-6 text-[#2f80ed]"
                          src="/images/rewards/active-star.svg"
                          alt="star"
                          height={20}
                        />
                      ) : (
                        <Image
                          width={20}
                          className="rotate-6 text-gray-300 dark:invert-100"
                          src="/images/rewards/unactive-star.svg"
                          alt="star"
                          height={20}
                        />
                      )}
                      <span
                        className={
                          activeIndexes.includes(idx)
                            ? "text-[#2f80ed]"
                            : "text-gray-400"
                        }
                      >
                        {day}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Test Points Section */}
        <div className="flex flex-col flex-1 min-w-[300px] border rounded-2xl p-5 dark:bg-[#0B1739] items-center min-h-[70vh]">
          <div className="flex justify-between w-full">
            <p className="font-bold mb-2 text-[#4F4F4F] dark:text-[#FDFDFD]">
              النقاط الاختبارات
            </p>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <div className="flex min-w-fit text-gray-500 gap-2 items-center cursor-pointer">
                  <span>{selectedRangeTestPoints}</span>
                  <ChevronDownIcon className="size-4" />
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {ranges.map((range) => (
                  <DropdownMenuItem
                    key={range}
                    onClick={() => handleSelectTestPoints(range)}
                  >
                    {range}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {isLoadingPointsTotal || isLoadingPointsSummary ? (
            <>
              {/* Points Summary Skeleton */}
              <div className="mb-6">
                <div className="h-14 w-36 mx-auto bg-gray-200 rounded-xl animate-pulse mb-2"></div>
                <div className="h-4 w-1/4 mx-auto bg-gray-200 rounded-full animate-pulse"></div>
              </div>

              {/* Chart Skeleton */}
              <div className="flex justify-around items-end w-full max-w-[430px] flex-1 px-3">
                {[...Array(7)].map((_, i) => (
                  <div key={i} className="flex flex-col items-center h-[90%]">
                    <div className="w-3 bg-gray-200 rounded-2xl overflow-hidden h-full relative">
                      <div
                        className="absolute bottom-0 w-full bg-gray-300 animate-pulse"
                        style={{ height: `${30 + i * 10}%` }}
                      ></div>
                    </div>
                    <div className="h-3 w-10 mt-2 bg-gray-200 rounded-full animate-pulse"></div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              <div>
                <div className="font-bold text-center text-[#074182] dark:text-[#3D93F5] text-4xl mb-2">
                  {selectedRangeTestPoints === "نقاط اليوم" && todayTotal}
                  {selectedRangeTestPoints === "هذا الأسبوع" && thisWeekTotal}
                  {selectedRangeTestPoints === "الشهر الماضي" && lastMonthTotal}
                  {selectedRangeTestPoints === "آخر 90 يوم" && last90DaysTotal}
                  {selectedRangeTestPoints === "الأسبوع الماضي" &&
                    lastWeekQuery}
                </div>
                <p className="text-sm text-center text-gray-500 mb-4">نقطة</p>
              </div>

              <div className="flex justify-around items-end h-full flex-1 px-3 min-w-fit w-[400px] max-w-[430px]">
                {testingChartData.map((item, index) => (
                  <div
                    key={index}
                    className="text-center h-[95%] flex flex-col items-center"
                  >
                    <div className="w-3 bg-gray-200 rounded-2xl overflow-hidden h-[281px] relative">
                      <div
                        className="absolute bottom-0 w-full bg-[#2f80ed] rounded-b-2xl"
                        style={{ height: `${item.percent}%` }}
                      />
                    </div>
                    <div
                      className={`text-xs mt-2 ${
                        todayIndex === index &&
                        selectedRangeTestPoints === "هذا الأسبوع"
                          ? "text-[#3D93F5]"
                          : ""
                      }`}
                    >
                      {item.day}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Store Section */}
      <div className="border p-5 rounded-2xl flex flex-col dark:bg-[#0B1739]">
        <div className="mb-5">
          <div className="flex gap-1 mb-3 justify-center items-center w-fit">
            <Image
              src="/images/rewards/Shopping_Bag.png"
              width={24}
              alt="shopping"
              height={24}
              className="size-8 align-middle dark:invert-100"
            />
            <p className="font-bold align-middle">متجر المكافآت</p>
          </div>
          <p className="text-2xl text-gray-500 dark:text-[#FDFDFD]">
            استبدل النقاط مقابل مكافئة
          </p>
        </div>

        <div className="grid justify-around w-full lg:grid-cols-[repeat(auto-fill,minmax(300px,483px))] gap-4">
          {isLoadingStore
            ? [...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="flex-col sm:flex-row items-center border rounded-[8px] p-4 flex gap-6 justify-between"
                >
                  <div className="flex items-center justify-between mt-4">
                    <div className="w-40 h-40 bg-gray-200 rounded-xl animate-pulse"></div>
                  </div>
                  <div className="flex flex-col gap-4 flex-1">
                    <div className="h-7 w-3/4 bg-gray-200 rounded-full animate-pulse"></div>
                    <div className="space-y-2">
                      <div className="h-4 w-full bg-gray-200 rounded-full animate-pulse"></div>
                      <div className="h-4 w-2/3 bg-gray-200 rounded-full animate-pulse"></div>
                    </div>
                    <div className="h-14 w-full bg-gray-200 rounded-lg animate-pulse mt-2"></div>
                  </div>
                </div>
              ))
            : storeItems.map((item, index) => (
                <div
                  key={item.id}
                  className="flex-col sm:flex-row items-center border rounded-[8px] p-4 hover:border-[#9EC9FA] sm:items-start hover:bg-[#9ec9fa3d] dark:hover:bg-[unset] flex gap-6 justify-between"
                >
                  <div className="flex items-center justify-between mt-4">
                    <Image
                      src={item.image_url || "/images/gift.png"}
                      alt="كأس"
                      width={0}
                      height={0}
                      style={{ width: "auto", height: "auto" }}
                      sizes="(max-width: 768px) 100vw, 13rem"
                      className="max-w-[170px]"
                    />
                  </div>

                  <div className="flex flex-col gap-2.5 h-full justify-around">
                    <p className="font-bold mb-1 text-2xl">{item.title}</p>
                    <p className="text-[1.2rem] text-gray-600">{item.desc}</p>
                    {typeof item.id === "number" &&
                    PurchasedItemsIds.includes(item.id) ? (
                      <div className="text-green-600 font-semibold text-[1.2rem] h-14 flex items-center justify-center rounded-lg border border-green-500 bg-green-100">
                        تم الاستبدال
                      </div>
                    ) : (
                      <Button
                        onClick={() => {
                          setSelectedReward({
                            id: item.id || index,
                            title: item.title,
                            points: item.points,
                          });
                          setShowConfirm(true);
                          setIsConfirmed(false);
                        }}
                        className="bg-[#074182] text-[1.2rem] py-2.5 text-white h-14 rounded-lg hover:bg-[#053866]"
                      >
                        استبدال
                      </Button>
                    )}
                  </div>
                </div>
              ))}
        </div>
      </div>

      {/* Purchase Confirmation Modal */}
      {showConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={() => setShowConfirm(false)}
        >
          <div
            className="bg-white dark:bg-[#0B1739] rounded-[14px] max-w-[400px] max-h-[60vh] h-300px flex flex-col justify-around w-full px-6 py-8 text-center shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            {!isConfirmed ? (
              <>
                <h2 className="font-bold text-[#212121] mb-2 text-2xl dark:text-white">
                  هل أنت متأكد من استبدال النقاط؟
                </h2>
                <p className="text-gray-600 mb-6 text-2xl">
                  سيتم خصم {selectedReward?.points} نقطة مقابل المكافأة.
                </p>
                <div className="flex gap-4 justify-center border-t pt-4">
                  <button
                    className="text-[#074182] font-bold border border-[#074182] rounded-lg px-6 py-2 text-sm hover:bg-[#f5faff]"
                    onClick={() => setShowConfirm(false)}
                    disabled={isPurchasing}
                  >
                    إلغاء
                  </button>
                  <button
                    className="bg-[#074182] text-white font-bold rounded-lg px-6 py-2 hover:bg-[#053866] text-2xl disabled:opacity-50"
                    onClick={handlePurchase}
                    disabled={isPurchasing}
                  >
                    {isPurchasing ? "جاري المعالجة..." : "تأكيد"}
                  </button>
                </div>
              </>
            ) : (
              <>
                <h2 className="font-bold text-[#212121] mb-2 text-2xl dark:text-white">
                  تم استبدال النقاط
                </h2>
                <p className="text-gray-600 mb-6 text-2xl">
                  ستحصل على مكافأتك قريباً.
                </p>
                <div className="border-t pt-4">
                  <button
                    className="w-full text-[#074182] dark:hover:text-[#074182] font-bold py-2 text-sm flex justify-center items-center gap-2 hover:bg-[#f5faff] rounded-lg dark:text[#fff]"
                    onClick={() => {
                      setShowConfirm(false);
                      setIsConfirmed(false);
                    }}
                  >
                    اغلاق
                    <span className="text-base">✕</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RewardsDashboard;
