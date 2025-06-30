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
  getPointsSummary,
  getRewardStoreItems,
  getStudyDaysLog,
  purchaseRewardItem,
} from "@/services/gamification.service";
import {
  PaginatedDailyPointSummaryResponse,
  PaginatedStudyDayLogResponse,
} from "@/types/api/gamification.types";
import { ChevronDownIcon } from "@heroicons/react/24/outline";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import Image from "next/image";
import { useEffect, useState } from "react";
import { toast } from "sonner";
// Type definitions
type PointsData = {
  day: string;
  percent: number;
};

type StoreItem = {
  id?: number | string;
  title: string;
  desc: string;
  points: number;
};

type GamificationSummary = {
  current_streak: number;
};

type PointsSummary = {
  points: number;
};

type RewardItem = {
  id: number | string;
  name: string;
  description: string;
  cost_points: number;
};

type Badge = {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon_url: string;
  criteria_description: string;
  is_earned: boolean;
  earned_at: string;
};

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
      refetchInterval: 60000,
      refetchIntervalInBackground: true,
    });

    const thisWeekQuery = useQuery({
      queryKey: ["points-total", "this-week"],
      queryFn: () => fetchPointsTotal(weekStart, weekEnd),
      refetchInterval: 60000,
      refetchIntervalInBackground: true,
    });
    const lastWeekQuery = useQuery({
      queryKey: ["points-total", "last-week"],
      queryFn: () => fetchPointsTotal(lastWeekStart, lastWeekEnd),
      refetchInterval: 60000,
      refetchIntervalInBackground: true,
    });
    const lastMonthQuery = useQuery({
      queryKey: ["points-total", "last-month"],
      queryFn: () => fetchPointsTotal(monthStart, monthEnd),
      refetchInterval: 60000,
      refetchIntervalInBackground: true,
    });

    const last90DaysQuery = useQuery({
      queryKey: ["points-total", "last-90-days"],
      queryFn: () => fetchPointsTotal(last90Days, today),
      refetchInterval: 60000,
      refetchIntervalInBackground: true,
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
    // isLoadingPointsTotal,
  } = usePointsTotals();

  // end the madaka
  const defaultStoreItems: StoreItem[] = [
    {
      title: "تصاميم",
      desc: "استبدل 20 نقطة مقابل الحصول على تصاميم، شرح وافٍ لما ستحصل عليه.",
      points: 20,
    },
    {
      title: "الدخول للمسابقة الكبرى",
      desc: "استبدل 30 نقطة مقابل الدخول للمسابقة الكبرى، التي سيتم الإعلان عنها لاحقاً.",
      points: 30,
    },
    {
      title: "أشعار",
      desc: "استبدل 10 نقاط مقابل الحصول على أشعار، شرح وافٍ لما ستحصل عليه.",
      points: 10,
    },
    {
      title: "مخطوطة",
      desc: "استبدل 5 نقاط مقابل الحصول على مخطوطة، شرح وافٍ لما ستحصل عليه.",
      points: 5,
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
  const { data: summaryData } = useQuery<GamificationSummary>({
    queryKey: ["gamificationSummary"],
    queryFn: getGamificationSummary,
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
  });
  // start days summary
  const { data: PointsSummary } = useQuery<PaginatedDailyPointSummaryResponse>({
    queryKey: ["PointsSummary"],
    queryFn: getPointsSummary,
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
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

  const dayPointsMap: Record<string, number> = {};

  results.forEach(({ date, total_points }) => {
    const dayIndex = new Date(date).getDay();
    const dayName = daysMap[dayIndex];
    dayPointsMap[dayName] = total_points;
  });

  const fullWeek: PointsData[] = Object.values(daysMap).map((day) => ({
    day,
    percent: dayPointsMap[day] ?? 0,
  }));
  const [activeIndexes, setActiveIndexes] = useState<number[]>([]);

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
  }, [fullWeek, activeIndexes]);
  console.log(activeIndexes);

  // end of  days summary
  const [testPoints] = useState(fullWeek);

  const { data: badgesData } = useQuery<Badge[]>({
    queryKey: ["myBadges"],
    queryFn: getAllBadges,
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
  });
  const { data: studyDaysData } = useQuery<PaginatedStudyDayLogResponse>({
    queryKey: ["StudyDaysLog"],
    queryFn: () => getStudyDaysLog(),
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
  });
  //try
  const studiedDays = studyDaysData?.results.map((item) => {
    const date = dayjs(item.study_date);
    const dayIndex = date.day(); // Sunday = 0, Monday = 1, ...
    const arabicDays = [
      "الأحد",
      "الإثنين",
      "الثلاثاء",
      "الأربعاء",
      "الخميس",
      "الجمعة",
      "السبت",
    ];
    return dayIndex;
  });

  //end the try
  const { data: pointsData } = useQuery<PointsSummary>({
    queryKey: ["pointsSummary"],
    queryFn: getPointsSummary,
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
  });

  const { data: storeData } = useQuery<RewardItem[]>({
    queryKey: ["rewardStoreItems"],
    queryFn: getRewardStoreItems,
    refetchInterval: 60000,
    refetchIntervalInBackground: true,
  });

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
        }))
      : defaultStoreItems;

  // Handle reward purchase
  const handlePurchase = async () => {
    if (!selectedReward) return;

    setIsPurchasing(true);
    try {
      await purchaseRewardItem(selectedReward.id);
      setIsConfirmed(true);
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
            <div className="flex justify-center gap-2 text-[24px] leading-none ">
              {["🥇", "🥈", "🏆", "🌟", "🎗️", "🌞", "🎯", "🏅", "👑"].map(
                (emoji, index) => {
                  const badge = myBadges[index];

                  const isEarned =
                    selectedRangeBadgRanges == "الكل"
                      ? true
                      : badge?.is_earned === true;
                  const description =
                    badge?.description ?? "لم يتم الحصول على هذه الشارة بعد";

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
                          src="badge.icon_url"
                        />
                      ) : (
                        emoji
                      )}
                    </span>
                  );
                }
              )}
            </div>
          </div>

          {/* Streak Card */}
          <div className="rounded-[20px] border border-[#E0E0E0] bg-white dark:bg-[#0B1739] px-5 py-6 shadow-sm space-y-5 max-w-[400px]">
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
                {studyDaysData?.count || 0} أيام متتالية
              </span>
            </div>

            {/* Progress */}
            <div className="flex items-center gap-2 mt-1 pr-12">
              <div className="w-full max-w-[200px] h-2 bg-gray-300 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#2f80ed]"
                  style={{
                    width: `${Math.min(
                      100,
                      ((studyDaysData?.count ?? 0) / 7) * 100
                    )}%`,
                  }}
                />
              </div>
              <span className="text-xs font-medium text-gray-600">
                {studyDaysData ? studyDaysData.count:"0"}/7
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
                  {activeIndexes.includes(idx) ? (
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
          <div>
            <div className="font-bold text-center text-[#074182] dark:text-[#3D93F5] text-4xl mb-2">
              {selectedRangeTestPoints === "نقاط اليوم" && todayTotal}
              {selectedRangeTestPoints === "هذا الأسبوع" && thisWeekTotal}
              {selectedRangeTestPoints === "الشهر الماضي" && lastMonthTotal}
              {selectedRangeTestPoints === "آخر 90 يوم" && last90DaysTotal}
              {selectedRangeTestPoints === "الأسبوع الماضي" && lastWeekQuery}
            </div>
            <p className="text-sm text-center text-gray-500 mb-4">نقطة</p>
          </div>

          <div className="flex justify-around items-end h-full flex-1 px-3 min-w-fit w-[400px] max-w-[430px]">
            {fullWeek.map((item, index) => (
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
                    todayIndex === index ? "text-[#3D93F5]" : ""
                  }`}
                >
                  {item.day}
                </div>
              </div>
            ))}
          </div>
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
          {storeItems.map((item, index) => (
            <div
              key={index}
              className="flex-col sm:flex-row items-center border rounded-[8px] p-4 hover:border-[#9EC9FA] sm:items-start hover:bg-[#9ec9fa3d] dark:hover:bg-[unset] flex gap-6 justify-between"
            >
              <div className="flex items-center justify-between mt-4">
                <Image
                  src="/images/gift.png"
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
