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
  PurchasedItem,
  PurchasedItemResponse,
  RewardStoreItem,
  StoreItemGamificaiton,
} from "@/types/api/gamification.types";
import { ChevronDownIcon, XMarkIcon, PlusIcon, TrashIcon } from "@heroicons/react/24/outline";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { format, parseISO, subDays } from "date-fns";
import dayjs from "dayjs";
import Image from "next/image";
import { useEffect, useMemo, useState, useRef, useLayoutEffect } from "react";
import { toast } from "sonner";
import { gsap } from "gsap";

const RewardsDashboard = () => {
  const todayIndex = new Date().getDay();
  
  // Refs for GSAP animations
  const titleRef = useRef(null);
  const badgesCardRef = useRef(null);
  const streakCardRef = useRef(null);
  const testPointsCardRef = useRef(null);
  const storeHeaderRef = useRef(null);
  const storeItemsRef = useRef<(HTMLDivElement | null)[]>([]);
  const examScoresRef = useRef(null);

  // New state for exam testing
  const [showExamTesting, setShowExamTesting] = useState(false);
  const [examScores, setExamScores] = useState<number[]>([]);
  const [currentScore, setCurrentScore] = useState<string>("");

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

  const defaultStoreItems: (StoreItemGamificaiton & {
    is_purchased: boolean;
    asset_file_url?: string | null;
  })[] = [
    {
      id: 0,
      title: "تصاميم",
      desc: "استبدل 20 نقطة مقابل الحصول على تصاميم، شرح وافٍ لما ستحصل عليه.",
      points: 20,
      image_url: "",
      is_purchased: false,
    },
    {
      id: 1,
      title: "الدخول للمسابقة الكبرى",
      desc: "استبدل 30 نقطة مقابل الدخول للمسابقة الكبرى، التي سيتم الإعلان عنها لاحقاً.",
      points: 30,
      image_url: "",
      is_purchased: false,
    },
    {
      id: 2,
      title: "أشعار",
      desc: "استبدل 10 نقاط مقابل الحصول على أشعار، شرح وافٍ لما ستحصل عليه.",
      points: 10,
      image_url: "",
      is_purchased: false,
    },
    {
      id: 3,
      title: "مخطوطة",
      desc: "استبدل 5 نقاط مقابل الحصول على مخطوطة، شرح وافٍ لما ستحصل عليه.",
      points: 5,
      image_url: "",
      is_purchased: false,
    },
  ];

  const [showConfirm, setShowConfirm] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [selectedReward, setSelectedReward] = useState<{
    id: number | string;
    title: string;
    points: number;
    image_url?: string;
    asset_file_url?: string;
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

  const { data: pointsData } = useQuery<PointsSummary>({
    queryKey: ["pointsSummary"],
    queryFn: getPointsSummary,
  });

  const { data: purchasedItemsData, refetch: refetchPurchasedItems } =
    useQuery<PurchasedItemResponse>({
      queryKey: ["getMyPurchasedItems"],
      queryFn: getMyPurchasedItems,
  });
  const { data: storeData, isLoading: isLoadingStore } = useQuery<
    RewardStoreItem[]
  >({
    queryKey: ["rewardStoreItems"],
    queryFn: getRewardStoreItems,
  });
  const queryClient = useQueryClient();

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
          asset_file_url: item.asset_file_url,
          is_purchased: item.is_purchased,
        }))
      : defaultStoreItems;

  // Handler functions for exam scores
  const handleAddScore = () => {
    const score = parseInt(currentScore);
    if (!isNaN(score) && score >= 0 && score <= 100) {
      setExamScores([...examScores, score]);
      setCurrentScore("");
    } else {
      toast.error("الرجاء إدخال درجة صحيحة بين 0 و 100");
    }
  };

  const handleRemoveScore = (index: number) => {
    setExamScores(examScores.filter((_, i) => i !== index));
  };

  const handleSaveScores = () => {
    // Here you would typically save the scores to your backend
    toast.success(`تم حفظ ${examScores.length} درجات الاختبار بنجاح`);
    // You can add API call here to save the scores
    // saveExamScores(examScores);
  };

  const calculateAverage = () => {
    if (examScores.length === 0) return 0;
    const sum = examScores.reduce((acc, score) => acc + score, 0);
    return (sum / examScores.length).toFixed(1);
  };

  // GSAP Animations
  useLayoutEffect(() => {
    const ctx = gsap.context(() => {
      // Title animation
      if (titleRef.current) {
        gsap.fromTo(titleRef.current, 
          { opacity: 0, y: -30 },
          { 
            opacity: 1, 
            y: 0, 
            duration: 0.8, 
            ease: "power3.out" 
          }
        );
      }

      // Badges card animation
      if (badgesCardRef.current) {
        gsap.fromTo(badgesCardRef.current,
          { opacity: 0, x: -50, scale: 0.9 },
          { 
            opacity: 1, 
            x: 0, 
            scale: 1,
            duration: 0.6,
            delay: 0.2,
            ease: "power2.out"
          }
        );
      }

      // Streak card animation
      if (streakCardRef.current) {
        gsap.fromTo(streakCardRef.current,
          { opacity: 0, x: -50, scale: 0.9 },
          { 
            opacity: 1, 
            x: 0,
            scale: 1, 
            duration: 0.6,
            delay: 0.4,
            ease: "power2.out"
          }
        );
      }

      // Test points card animation
      if (testPointsCardRef.current) {
        gsap.fromTo(testPointsCardRef.current,
          { opacity: 0, y: 50, scale: 0.95 },
          { 
            opacity: 1, 
            y: 0,
            scale: 1, 
            duration: 0.7,
            delay: 0.6,
            ease: "back.out(1.7)"
          }
        );
      }

      // Exam scores box animation
      if (examScoresRef.current && showExamTesting) {
        gsap.fromTo(examScoresRef.current,
          { opacity: 0, y: 30, scale: 0.95 },
          { 
            opacity: 1, 
            y: 0,
            scale: 1, 
            duration: 0.5,
            ease: "power2.out"
          }
        );
      }

      // Store header animation
      if (storeHeaderRef.current) {
        gsap.fromTo(storeHeaderRef.current,
          { opacity: 0, y: 30 },
          { 
            opacity: 1, 
            y: 0, 
            duration: 0.6,
            delay: 0.8,
            ease: "power2.out"
          }
        );
      }

      // Store items staggered animation
      const validStoreItems = storeItemsRef.current.filter((el): el is HTMLDivElement => el !== null);
      if (validStoreItems.length > 0) {
        gsap.fromTo(validStoreItems,
          { 
            opacity: 0, 
            y: 40,
            scale: 0.9
          },
          { 
            opacity: 1, 
            y: 0,
            scale: 1,
            duration: 0.5,
            stagger: 0.1,
            delay: 1,
            ease: "power2.out"
          }
        );
      }

      // Chart bars animation (when visible)
      const chartBars = document.querySelectorAll('.chart-bar');
      if (chartBars.length > 0) {
        gsap.fromTo(chartBars,
          { scaleY: 0, transformOrigin: "bottom" },
          { 
            scaleY: 1, 
            duration: 0.8,
            stagger: 0.05,
            delay: 1.2,
            ease: "power2.out"
          }
        );
      }

      // Badge emojis animation
      const badgeEmojis = document.querySelectorAll('.badge-emoji');
      if (badgeEmojis.length > 0) {
        gsap.fromTo(badgeEmojis,
          { scale: 0, rotation: -180 },
          { 
            scale: 1,
            rotation: 0, 
            duration: 0.5,
            stagger: 0.05,
            delay: 0.8,
            ease: "back.out(1.7)"
          }
        );
      }

      // Star icons animation
      const starIcons = document.querySelectorAll('.star-icon');
      if (starIcons.length > 0) {
        gsap.fromTo(starIcons,
          { scale: 0, opacity: 0 },
          { 
            scale: 1,
            opacity: 1, 
            duration: 0.4,
            stagger: 0.08,
            delay: 1,
            ease: "elastic.out(1, 0.5)"
          }
        );
      }
    });

    return () => ctx.revert();
  }, [isLoadingBadges, isLoadingStore, isLoadingPointsTotal, showExamTesting]);

  const handlePurchase = async () => {
    if (!selectedReward) return;

    setIsPurchasing(true);
    try {
      await purchaseRewardItem(selectedReward.id);
      setIsConfirmed(true);

      queryClient.setQueryData<RewardStoreItem[]>(
        ["rewardStoreItems"],
        (oldData) => {
          if (!oldData) return oldData;
          return oldData.map((item) =>
            item.id === selectedReward.id
              ? { ...item, is_purchased: true }
              : item
          );
        }
      );

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

  const handleViewImage = (imageUrl: string) => {
    window.open(imageUrl, "_blank");
  };

  const handleViewAsset = (assetUrl: string) => {
    window.open(assetUrl, "_blank");
  };
  const testingChartData =
    selectedRangeTestPoints === "الأسبوع الماضي"
      ? myLastWeekData || fullWeek
      : selectedRangeTestPoints === "نقاط اليوم"
      ? fullWeek.filter((_, index) => index === todayIndex)
      : fullWeek;

  return (
    <div className="py-5 sm:p-5 space-y-6 dark:bg-[#081028]">
      <h1 ref={titleRef} className="text-4xl pr-3 font-bold leading-9">
        مكافآت المذاكرة والمسابقات
      </h1>
      
      {/* Test Your Abilities Section */}
      <div className="border rounded-2xl p-5 dark:bg-[#0B1739] bg-white">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-[#074182] dark:text-[#3D93F5]">
            هل تختبر قدراتك؟
          </h2>
          <div className="flex gap-3">
            <button
              onClick={() => setShowExamTesting(true)}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                showExamTesting 
                  ? "bg-[#074182] text-white" 
                  : "border border-[#074182] text-[#074182] hover:bg-[#f5faff]"
              }`}
            >
              نعم
            </button>
            <button
              onClick={() => setShowExamTesting(false)}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                !showExamTesting 
                  ? "bg-gray-500 text-white" 
                  : "border border-gray-500 text-gray-500 hover:bg-gray-50"
              }`}
            >
              لا
            </button>
          </div>
        </div>

        {/* Exam Scores Input Box */}
        {showExamTesting && (
          <div ref={examScoresRef} className="mt-6 p-6 bg-gray-50 dark:bg-[#081028] rounded-xl">
            <h3 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">
              أدخل درجات الاختبارات السابقة
            </h3>
            
            {/* Input Section */}
            <div className="flex gap-3 mb-4">
              <input
                type="number"
                min="0"
                max="100"
                value={currentScore}
                onChange={(e) => setCurrentScore(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddScore()}
                placeholder="أدخل الدرجة (0-100)"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#074182] dark:bg-[#0B1739] dark:border-gray-600 dark:text-white"
              />
              <button
                onClick={handleAddScore}
                className="px-4 py-2 bg-[#074182] text-white rounded-lg hover:bg-[#053866] flex items-center gap-2"
              >
                <PlusIcon className="w-5 h-5" />
                إضافة
              </button>
            </div>

            {/* Scores List */}
            {examScores.length > 0 && (
              <div className="space-y-3 mb-4">
                <div className="font-medium text-gray-700 dark:text-gray-300">
                  الدرجات المدخلة:
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {examScores.map((score, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between px-3 py-2 bg-white dark:bg-[#0B1739] border border-gray-200 dark:border-gray-600 rounded-lg group"
                    >
                      <span className="font-medium text-lg">
                        {score}
                        <span className="text-sm text-gray-500 mr-1">%</span>
                      </span>
                      <button
                        onClick={() => handleRemoveScore(index)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-red-500 hover:text-red-700"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Statistics */}
                <div className="flex gap-6 mt-4 p-4 bg-white dark:bg-[#0B1739] rounded-lg">
                  <div>
                    <span className="text-gray-500 text-sm">عدد الاختبارات:</span>
                    <span className="font-bold text-xl mr-2 text-[#074182] dark:text-[#3D93F5]">
                      {examScores.length}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">المتوسط:</span>
                    <span className="font-bold text-xl mr-2 text-[#074182] dark:text-[#3D93F5]">
                      {calculateAverage()}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">أعلى درجة:</span>
                    <span className="font-bold text-xl mr-2 text-green-600">
                      {examScores.length > 0 ? Math.max(...examScores) : 0}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">أقل درجة:</span>
                    <span className="font-bold text-xl mr-2 text-red-600">
                      {examScores.length > 0 ? Math.min(...examScores) : 0}%
                    </span>
                  </div>
                </div>

                {/* Save Button */}
                <div className="flex justify-center mt-4">
                  <button
                    onClick={handleSaveScores}
                    className="px-8 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors"
                  >
                    حفظ الدرجات
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-6 justify-center">
        {/* Achievement and Weekly Stars Section */}
        <div className="min-w-[300px] space-y-6 font-sans text-right">
          {/* Badges Card */}
          <div ref={badgesCardRef} className="rounded-[20px] border border-[#E0E0E0] bg-white dark:bg-[#0B1739] px-5 py-6 shadow-sm space-y-5 max-w-[400px]">
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
                          className={`badge-emoji ${
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
          <div ref={streakCardRef} className="rounded-[20px] border border-[#E0E0E0] bg-white dark:bg-[#0B1739] px-5 py-6 shadow-sm space-y-5 max-w-[400px]">
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
                          className="rotate-6 text-[#2f80ed] star-icon"
                          src="/images/rewards/active-star.svg"
                          alt="star"
                          height={20}
                        />
                      ) : (
                        <Image
                          width={20}
                          className="rotate-6 text-gray-300 dark:invert-100 star-icon"
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
        <div ref={testPointsCardRef} className="flex flex-col flex-1 min-w-[300px] border rounded-2xl p-5 dark:bg-[#0B1739] items-center min-h-[70vh]">
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
                        className="absolute bottom-0 w-full bg-[#2f80ed] rounded-b-2xl chart-bar"
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
        <div ref={storeHeaderRef} className="mb-5">
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
                  ref={(el:any) => storeItemsRef.current[i] = el}
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
                  ref={(el:any) => storeItemsRef.current[index] = el}
                  className="flex-col sm:flex-row items-center border rounded-[8px] p-4 hover:border-[#9EC9FA] sm:items-start hover:bg-[#9ec9fa3d] dark:hover:bg-[unset] flex gap-6 justify-between"
                >
                  <div className="flex items-center justify-between mt-4">
                    <Image
                      src={"/images/gift.png"}
                      alt="كأس"
                      width={0}
                      height={0}
                      style={{ width: "auto", height: "auto" }}
                      sizes="(max-width: 768px) 100vw, 13rem"
                      className="max-w-[170px]"
                    />
                  </div>

                  <div className="flex flex-col gap-2.5 h-full justify-around">
                    <div className="flex items-center gap-2">
                      <p className="font-bold mb-1 text-2xl">{item.title}</p>
                      {item.is_purchased && (
                        <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 min-w-fit py-0.5 rounded-full border border-green-200">
                          تم الشراء
                        </span>
                      )}
                    </div>
                    <p className="text-[1.2rem] text-gray-600">{item.desc}</p>
                    {item.is_purchased ? (
                      <div className="flex justify-center gap-2">
                        {item.image_url && (
                          <Button
                            onClick={() => handleViewImage(item.image_url!)}
                            className="bg-[#007bff] text-[1.1rem] py-2 text-white h-12 rounded-lg hover:bg-[#0056b3]"
                          >
                            عرض الصورة
                          </Button>
                        )}
                        {item.asset_file_url && (
                          <Button
                            onClick={() =>
                              handleViewAsset(item.asset_file_url!)
                            }
                            className="bg-[#28a745] text-[1.1rem] py-2 text-white h-12 rounded-lg hover:bg-[#218838]"
                          >
                            عرض الملف
                          </Button>
                        )}
                        {item.is_purchased &&
                          !item.image_url &&
                          !item.asset_file_url && (
                            <div className="text-gray-500 text-center py-2 text-sm">
                              لا يوجد ملف أو صورة متاحة
                            </div>
                          )}
                      </div>
                    ) : (
                      <Button
                        onClick={() => {
                          setSelectedReward({
                            id: item.id || index,
                            title: item.title,
                            points: item.points,
                            image_url: item.image_url || undefined,
                            asset_file_url: item.asset_file_url || undefined,
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
            className="bg-white dark:bg-[#0B1739] rounded-[14px] max-w-[400px] max-h-[60vh] h-300px flex flex-col justify-around w-full px-6 py-8 text-center shadow-lg modal-entrance"
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
                <p className="text-gray-600 mb-4 text-lg">
                  تم شراء "{selectedReward?.title}" بنجاح!
                </p>

                {/* Action Buttons */}
                <div className="flex flex-col gap-3 mb-4">
                  {selectedReward?.image_url && (
                    <Button
                      onClick={() => handleViewImage(selectedReward.image_url!)}
                      className="bg-[#007bff] text-white h-12 rounded-lg hover:bg-[#0056b3]"
                    >
                      عرض الصورة
                    </Button>
                  )}
                  {selectedReward?.asset_file_url && (
                    <Button
                      onClick={() =>
                        handleViewAsset(selectedReward.asset_file_url!)
                      }
                      className="bg-[#28a745] text-white h-12 rounded-lg hover:bg-[#218838]"
                    >
                      عرض الملف
                    </Button>
                  )}
                  {!selectedReward?.image_url &&
                    !selectedReward?.asset_file_url && (
                      <p className="text-gray-500 text-center text-sm">
                        لا يوجد ملف أو صورة متاحة لهذا العنصر
                      </p>
                    )}
                </div>

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

      <style jsx>{`
        @keyframes modalEntrance {
          from {
            opacity: 0;
            transform: scale(0.9) translateY(20px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        
        .modal-entrance {
          animation: modalEntrance 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default RewardsDashboard;
