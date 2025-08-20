"use client";

import React, { useMemo, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { gsap } from "gsap";
import {
  AlertTriangle,
  Clock,
  FileText,
  Loader2,
  CheckCircle,
  XCircle,
  HelpCircle,
  BarChart3,
  ThumbsUp,
  ListTree,
  TrendingUp,
  Award,
  Sparkles,
  Flame,
  Target,
  BookOpenCheck,
  PlusCircle,
  Star,
  Trophy,
  Zap,
  Crown,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthActions, useAuthStore } from "@/store/auth.store";
import { UserProfile } from "@/types/api/auth.types";

import { getTestAttemptReview } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import {
  UserTestAttemptCompletionResponse,
  UserTestAttemptReviewResponse,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";

interface QualitativeLevelInfo {
  text: string;
  colorClass: string;
  IconComponent: React.ElementType;
}

// This helper can be reused from the level assessment score page
const getQualitativeLevelInfo = (
  percentage: number | null,
  tLevel: any
): QualitativeLevelInfo => {
  const defaultLevel = {
    text: tLevel("notAvailable"),
    colorClass: "text-muted-foreground",
    IconComponent: HelpCircle,
  };
  if (percentage === null) return defaultLevel;

  if (percentage >= 90)
    return {
      text: tLevel("excellent"),
      colorClass: "text-green-600 dark:text-green-500",
      IconComponent: Crown,
    };
  if (percentage >= 80)
    return {
      text: tLevel("veryGood"),
      colorClass: "text-sky-600 dark:text-sky-500",
      IconComponent: Trophy,
    };
  if (percentage >= 70)
    return {
      text: tLevel("good"),
      colorClass: "text-blue-600 dark:text-blue-500",
      IconComponent: Star,
    };
  if (percentage >= 50)
    return {
      text: tLevel("acceptable"),
      colorClass: "text-yellow-500 dark:text-yellow-400",
      IconComponent: AlertTriangle,
    };
  return {
    text: tLevel("weak"),
    colorClass: "text-red-600 dark:text-red-500",
    IconComponent: XCircle,
  };
};

const TraditionalLearningScorePage = () => {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const t = useTranslations("Study.traditionalLearning.score");
  const tLevel = useTranslations("Study.determineLevel.badgeColors");
  const tCommon = useTranslations("Common");

  const attemptId = params.attemptId as string;

  const { user } = useAuthStore();
  const { updateUserProfile } = useAuthActions();
  const hasUpdatedProfileRef = useRef(false);

  // GSAP Animation Refs
  const cardRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const scoreRef = useRef<HTMLDivElement>(null);
  const pointsCardRef = useRef<HTMLDivElement>(null);
  const streakCardRef = useRef<HTMLDivElement>(null);
  const badgesCardRef = useRef<HTMLDivElement>(null);
  const statsCardsRef = useRef<HTMLDivElement>(null);
  const performanceRef = useRef<HTMLDivElement>(null);
  const analysisRef = useRef<HTMLDivElement>(null);
  const footerRef = useRef<HTMLDivElement>(null);

  // 1. Attempt to get fresh data passed from the previous page
  const completionData =
    queryClient.getQueryData<UserTestAttemptCompletionResponse>(
      queryKeys.tests.completionResult(attemptId)
    );

  // 2. Fallback query if the page is loaded directly display
  const {
    data: reviewData,
    isLoading: isLoadingReview,
    error,
  } = useQuery<UserTestAttemptReviewResponse, Error>({
    queryKey: queryKeys.tests.review(attemptId),
    queryFn: () => getTestAttemptReview(attemptId),
    enabled: !!attemptId && !completionData,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // GSAP Animation Functions
  const animateScoreReveal = (score: number) => {
    if (!scoreRef.current) return;
    
    const scoreElement = scoreRef.current.querySelector('.score-number');
    if (!scoreElement) return;

    // Animate score counting up
    gsap.fromTo(scoreElement, 
      { textContent: "0" },
      {
        textContent: score.toFixed(0),
        duration: 2,
        ease: "power2.out",
        snap: { textContent: 1 },
        onUpdate: function() {
          const current = Math.round(+this.targets()[0].textContent);
          // Change color based on score during animation
          if (current >= 90) {
            gsap.set(scoreRef.current, { className: "inline-flex items-center rounded-full bg-green-500 px-6 py-3 text-3xl font-bold text-white shadow-lg animate-pulse" });
          } else if (current >= 70) {
            gsap.set(scoreRef.current, { className: "inline-flex items-center rounded-full bg-blue-500 px-6 py-3 text-3xl font-bold text-white shadow-lg animate-pulse" });
          } else if (current >= 50) {
            gsap.set(scoreRef.current, { className: "inline-flex items-center rounded-full bg-yellow-500 px-6 py-3 text-3xl font-bold text-white shadow-lg animate-pulse" });
          } else {
            gsap.set(scoreRef.current, { className: "inline-flex items-center rounded-full bg-red-500 px-6 py-3 text-3xl font-bold text-white shadow-lg animate-pulse" });
          }
        }
      }
    );

    // Pulse animation for score circle
    gsap.to(scoreRef.current, {
      duration: 0.6,
      ease: "power2.inOut",
      repeat: 2,
      delay: 1.5
    });
  };

  const animatePointsCounter = (points: number) => {
    if (!pointsCardRef.current) return;
    
    const pointsElement = pointsCardRef.current.querySelector('.points-number');
    if (!pointsElement) return;

    // Sparkle effect
    gsap.to(pointsCardRef.current, {
      boxShadow: "0 0 20px rgba(234, 179, 8, 0.5)",
      duration: 0.5,
      yoyo: true,
      repeat: 3,
      delay: 0.5
    });

    // Count up animation
    gsap.fromTo(pointsElement,
      { textContent: "0" },
      {
        textContent: points.toString(),
        duration: 1.5,
        ease: "power2.out",
        snap: { textContent: 1 },
        delay: 0.8
      }
    );

    // Floating sparkles effect
    for (let i = 0; i < 5; i++) {
      const sparkle = document.createElement('div');
      sparkle.innerHTML = '✨';
      sparkle.className = 'absolute text-yellow-400 pointer-events-none';
      sparkle.style.fontSize = '20px';
      pointsCardRef.current.appendChild(sparkle);
      
      gsap.fromTo(sparkle, 
        { 
          x: Math.random() * 100 - 50,
          y: 0,
          opacity: 1,
          scale: 0
        },
        {
          x: Math.random() * 200 - 100,
          y: -100,
          opacity: 0,
          scale: 1,
          duration: 2,
          ease: "power2.out",
          delay: 1 + (i * 0.2),
          onComplete: () => sparkle.remove()
        }
      );
    }
  };

  const animateStreakFlame = (days: number, updated: boolean) => {
    if (!streakCardRef.current) return;
    
    const flameIcon = streakCardRef.current.querySelector('.flame-icon');
    const daysElement = streakCardRef.current.querySelector('.streak-days');
    
    if (flameIcon) {
      // Flame flickering animation
      gsap.to(flameIcon, {
        duration: 2,
        ease: "power2.inOut",
        repeat: -1,
        yoyo: true
      });
      
      // Color transition based on streak
      if (days >= 7) {
        gsap.to(flameIcon, {
          filter: "hue-rotate(120deg)", // Blue flame for long streaks
          duration: 1,
          delay: 0.5
        });
      }
    }
    
    if (daysElement && updated) {
      // Bounce animation when streak is updated
      gsap.fromTo(daysElement,
        { scale: 0, rotation: -180 },
        { 
          scale: 1, 
          rotation: 0,
          duration: 0.8,
          ease: "back.out(1.7)",
          delay: 0.3
        }
      );
    }
  };

  const animateBadges = (badges: any[]) => {
    if (!badgesCardRef.current || !badges.length) return;
    
    const badgeElements = badgesCardRef.current.querySelectorAll('.badge-item');
    
    badgeElements.forEach((badge, index) => {
      gsap.fromTo(badge,
        { 
          scale: 0,
          rotation: 360,
          opacity: 0
        },
        {
          scale: 1,
          rotation: 0,
          opacity: 1,
          duration: 0.6,
          ease: "back.out(1.7)",
          delay: 1.2 + (index * 0.2)
        }
      );
      
      // Continuous glow effect
      gsap.to(badge, {
        duration: 2,
        repeat: -1,
        ease: "power2.inOut",
        delay: 2 + (index * 0.2)
      });
    });
  };

  const animateStatsCards = () => {
    if (!statsCardsRef.current) return;
    
    const cards = statsCardsRef.current.querySelectorAll('.stat-card');
    
    cards.forEach((card, index) => {
      gsap.fromTo(card,
        {
          y: 50,
          opacity: 0,
          scale: 0.8
        },
        {
          y: 0,
          opacity: 1,
          scale: 1,
          duration: 0.6,
          ease: "back.out(1.7)",
          delay: 1.8 + (index * 0.2)
        }
      );
      
      // Hover effect setup
      const icon = card.querySelector('.stat-icon');
      if (icon) {
        card.addEventListener('mouseenter', () => {
          gsap.to(icon, {
            scale: 1.2,
            rotation: 10,
            duration: 0.3,
            ease: "power2.out"
          });
          gsap.to(card, {
            scale: 1.05,
            duration: 0.3,
            ease: "power2.out"
          });
        });
        
        card.addEventListener('mouseleave', () => {
          gsap.to(icon, {
            scale: 1,
            rotation: 0,
            duration: 0.3,
            ease: "power2.out"
          });
          gsap.to(card, {
            scale: 1,
            duration: 0.3,
            ease: "power2.out"
          });
        });
      }
    });
  };

  const animatePerformanceSection = () => {
    if (!performanceRef.current) return;
    
    const performanceItems = performanceRef.current.querySelectorAll('.performance-item');
    
    performanceItems.forEach((item, index) => {
      gsap.fromTo(item,
        {
          x: -50,
          opacity: 0
        },
        {
          x: 0,
          opacity: 1,
          duration: 0.5,
          ease: "power2.out",
          delay: 2.5 + (index * 0.1)
        }
      );
    });
  };

  const animateInitialLoad = () => {
    const tl = gsap.timeline();
    
    // Set initial states
    gsap.set(cardRef.current, { scale: 0.8, opacity: 0, y: 50 });
    gsap.set(headerRef.current, { opacity: 0, y: -30 });
    gsap.set(scoreRef.current, { scale: 0, opacity: 0 });
    
    // Animate card entrance
    tl.to(cardRef.current, {
      scale: 1,
      opacity: 1,
      y: 0,
      duration: 0.8,
      ease: "back.out(1.7)"
    })
    .to(headerRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.5,
      ease: "power2.out"
    }, "-=0.3")
    .to(scoreRef.current, {
      scale: 1,
      opacity: 1,
      duration: 0.6,
      ease: "back.out(1.7)"
    }, "-=0.2");
  };

  // Gamification & Profile update logic
  useEffect(() => {
    if (completionData && user && !hasUpdatedProfileRef.current) {
      const totalPointsEarned =
        (completionData.points_from_test_completion_event ?? 0) +
        (completionData.points_from_correct_answers_this_test ?? 0);
      const newStreakDays = completionData.streak_info?.current_days;

      const profileUpdates: Partial<UserProfile> = {};
      if (totalPointsEarned > 0)
        profileUpdates.points = user.points + totalPointsEarned;
      if (
        newStreakDays !== undefined &&
        newStreakDays !== user.current_streak_days
      ) {
        profileUpdates.current_streak_days = newStreakDays;
      }

      if (Object.keys(profileUpdates).length > 0) {
        updateUserProfile(profileUpdates);
        queryClient.invalidateQueries({
          queryKey: queryKeys.gamification.pointsSummary(user.id),
        });
        queryClient.invalidateQueries({
          queryKey: queryKeys.gamification.studyDaysLog(user.id),
        });
        hasUpdatedProfileRef.current = true;
      }
    }
  }, [completionData, user, updateUserProfile, queryClient]);

  // Animation trigger effect
  useEffect(() => {
    if (!displayData) return;
    
    const timer = setTimeout(() => {
      animateInitialLoad();
      
      // Trigger specific animations based on data
      if (displayData.overallScore !== null) {
        animateScoreReveal(displayData.overallScore);
      }
      
      if (displayData.totalPointsEarned > 0) {
        animatePointsCounter(displayData.totalPointsEarned);
      }
      
      if (displayData.streak_info) {
        animateStreakFlame(displayData.streak_info.current_days, displayData.streak_info.updated);
      }
      
      if (displayData.badges_won && displayData.badges_won.length > 0) {
        animateBadges(displayData.badges_won);
      }
      
      animateStatsCards();
      animatePerformanceSection();
      
      // Footer animation
      if (footerRef.current) {
        gsap.fromTo(footerRef.current,
          { y: 30, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.6,
            ease: "power2.out",
            delay: 3
          }
        );
      }
      
      // Analysis section animation
      if (analysisRef.current) {
        gsap.fromTo(analysisRef.current,
          { scale: 0.95, opacity: 0 },
          {
            scale: 1,
            opacity: 1,
            duration: 0.6,
            ease: "power2.out",
            delay: 2.8
          }
        );
      }
      
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  const isLoading = isLoadingReview && !completionData;
  const combinedData = completionData || reviewData;

  const displayData = useMemo(() => {
    if (!combinedData) return null;

    // Data from a completed session (primary source)
    if ("score" in combinedData && combinedData.score) {
      const data = combinedData as UserTestAttemptCompletionResponse;
      const answeredCount = data.answered_question_count;
      const correctCount = data.correct_answers_in_test_count;
      return {
        overallScore: data.score.overall,
        results_summary: data.results_summary,
        smart_analysis: data.smart_analysis,
        badges_won: data.badges_won,
        streak_info: data.streak_info,
        totalQuestions: data.total_questions,
        correctAnswers: correctCount,
        answeredQuestionsCount: answeredCount,
        incorrectAnswers: answeredCount - correctCount,
        skippedAnswers: data.total_questions - answeredCount,
        totalPointsEarned:
          (data.points_from_test_completion_event ?? 0) +
          (data.points_from_correct_answers_this_test ?? 0),
        timeTakenMinutes: null,
      };
    }

    // Data from a review API call (fallback)
    const data = combinedData as UserTestAttemptReviewResponse;
    const totalQuestions = data.questions.length;
    const answeredCount = data.questions.filter(
      (q) => q.user_answer_details?.selected_choice !== null
    ).length;
    const correctCount = data.questions.filter(
      (q) => q.user_answer_details?.is_correct === true
    ).length;

    return {
      overallScore: data.score_percentage,
      results_summary: data.results_summary,
      smart_analysis: null,
      badges_won: [],
      streak_info: null,
      totalQuestions: totalQuestions,
      correctAnswers: correctCount,
      incorrectAnswers: answeredCount - correctCount,
      skippedAnswers: totalQuestions - answeredCount,
      totalPointsEarned: 0,
      timeTakenMinutes: data.time_taken_minutes ?? null,
    };
  }, [combinedData]);

  if (isLoading) return <ScorePageSkeleton />;

  if (error || !displayData) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert variant="destructive" className="max-w-md text-center">
          <AlertTriangle className="mx-auto mb-2 h-6 w-6" />
          <AlertTitle>{tCommon("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(error, t("errors.fetchReviewFailed"))}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const {
    overallScore,
    results_summary,
    smart_analysis,
    badges_won,
    streak_info,
    totalQuestions,
    correctAnswers,
    incorrectAnswers,
    skippedAnswers,
    totalPointsEarned,
    timeTakenMinutes,
  } = displayData;

  const levelInfo = getQualitativeLevelInfo(overallScore, tLevel);
  const AdviceIconComponent =
    smart_analysis && overallScore !== null && overallScore < 50
      ? AlertTriangle
      : ThumbsUp;

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card ref={cardRef} className="mx-auto max-w-4xl shadow-xl overflow-hidden">
        <CardHeader ref={headerRef} className="text-center relative">
          {/* Celebration particles */}
          <div className="absolute inset-0 pointer-events-none">
            {[...Array(20)].map((_, i) => (
              <div
                key={i}
                className="absolute w-2 h-2 bg-yellow-400 rounded-full opacity-0"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 3}s`,
                }}
              />
            ))}
          </div>
          
          <CardTitle className="text-2xl font-bold md:text-3xl relative z-10">
            {t("yourScoreIsReady")}
          </CardTitle>
          {overallScore !== null ? (
            <div className="mt-4">
              <span 
                ref={scoreRef}
                className="inline-flex items-center rounded-full bg-primary px-6 py-3 text-3xl font-bold text-primary-foreground shadow-lg"
              >
                <span className="score-number">0</span>
                <span className="ms-1 text-xl opacity-80">%</span>
              </span>
            </div>
          ) : (
            <div className="mt-4">
              <span className="inline-flex items-center rounded-full bg-muted px-6 py-3 text-2xl font-bold text-muted-foreground shadow-lg">
                {tCommon("status.notAvailableShort")}
              </span>
            </div>
          )}
        </CardHeader>

        <CardContent className="space-y-8 pt-6">
          {/* Enhanced Gamification Section */}
          {(totalPointsEarned > 0 ||
            (badges_won && badges_won.length > 0) ||
            streak_info) && (
            <>
              <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-3">
                {totalPointsEarned > 0 && (
                  <Card ref={pointsCardRef} className="p-4 relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-yellow-400/10 to-orange-500/10"></div>
                    <Zap className="mx-auto mb-2 h-8 w-8 text-yellow-500" />
                    <p className="text-sm text-muted-foreground">
                      {t("pointsEarned")}
                    </p>
                    <p className="text-xl font-bold flex items-center justify-center gap-2">
                      <span className="points-number">0</span>
                      <Sparkles className="h-5 w-5 text-yellow-500" />
                    </p>
                  </Card>
                )}
                {streak_info && (
                  <Card ref={streakCardRef} className="p-4 relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-orange-400/10 to-red-500/10"></div>
                    <Flame className="flame-icon mx-auto mb-2 h-8 w-8 text-orange-500" />
                    <p className="text-sm text-muted-foreground">
                      {t("currentStreak")}
                    </p>
                    <p className="text-xl font-bold flex items-center justify-center gap-2">
                      <span className="streak-days">{streak_info.current_days}</span>
                      <span className="text-sm">{t("days")}</span>
                      {streak_info.updated && (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      )}
                    </p>
                  </Card>
                )}
                {badges_won && badges_won.length > 0 && (
                  <Card ref={badgesCardRef} className="p-4 sm:col-span-2 lg:col-span-1 relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-indigo-400/10 to-purple-500/10"></div>
                    <Award className="mx-auto mb-2 h-8 w-8 text-indigo-500" />
                    <p className="text-sm text-muted-foreground">
                      {t("badgesUnlocked")}
                    </p>
                    <div className="mt-1 flex flex-wrap justify-center gap-2">
                      {badges_won.map((badge, index) => (
                        <Badge
                          key={badge.slug}
                          variant="secondary"
                          className="badge-item text-xs relative overflow-hidden"
                          title={badge.description}
                        >
                          <span className="relative z-10">{badge.name}</span>
                          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 to-purple-500/20"></div>
                        </Badge>
                      ))}
                    </div>
                  </Card>
                )}
              </div>
              <Separator />
            </>
          )}

          {/* Enhanced Core Stats Section */}
          <div ref={statsCardsRef} className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-3">
            <Card className="stat-card p-4 relative overflow-hidden group cursor-pointer">
              <div className="absolute inset-0 bg-gradient-to-br from-green-400/5 to-emerald-500/5 group-hover:from-green-400/10 group-hover:to-emerald-500/10 transition-all duration-300"></div>
              <levelInfo.IconComponent
                className={`stat-icon mx-auto mb-2 h-8 w-8 ${levelInfo.colorClass} relative z-10`}
              />
              <p className="text-sm text-muted-foreground relative z-10">
                {t("currentLevel")}
              </p>
              <p className={`text-xl font-bold ${levelInfo.colorClass} relative z-10`}>
                {levelInfo.text}
              </p>
            </Card>
            
            <Card className="stat-card p-4 relative overflow-hidden group cursor-pointer">
              <div className="absolute inset-0 bg-gradient-to-br from-green-400/5 to-green-600/5 group-hover:from-green-400/10 group-hover:to-green-600/10 transition-all duration-300"></div>
              <CheckCircle className="stat-icon mx-auto mb-2 h-8 w-8 text-green-500 relative z-10" />
              <p className="text-sm text-muted-foreground relative z-10">
                {t("correctAnswers")}
              </p>
              <p className="text-xl font-bold relative z-10">
                {correctAnswers}{" "}
                <span className="text-base text-muted-foreground">
                  /{totalQuestions || tCommon("status.notAvailableShort")}
                </span>
              </p>
            </Card>
            
            <Card className="stat-card p-4 relative overflow-hidden group cursor-pointer">
              <div className="absolute inset-0 bg-gradient-to-br from-red-400/5 to-red-600/5 group-hover:from-red-400/10 group-hover:to-red-600/10 transition-all duration-300"></div>
              <XCircle className="stat-icon mx-auto mb-2 h-8 w-8 text-red-500 relative z-10" />
              <p className="text-sm text-muted-foreground relative z-10">
                {t("incorrectAnswers")}
              </p>
              <p className="text-xl font-bold relative z-10">
                {incorrectAnswers}
                {skippedAnswers > 0 && (
                  <span className="ms-2 text-sm font-normal text-muted-foreground">
                    (+{skippedAnswers} {t("skipped")})
                  </span>
                )}
              </p>
            </Card>
          </div>

          {/* Enhanced Detailed Performance Section */}
          {results_summary && Object.keys(results_summary).length > 0 && (
            <div ref={performanceRef}>
              <h3 className="mb-4 text-center text-xl font-semibold">
                <Target className="me-2 inline-block h-6 w-6 rtl:me-0 rtl:ms-2" />
                {t("detailedPerformance")}
              </h3>
              <Card className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400/5 to-indigo-500/5"></div>
                <CardContent className="max-h-80 space-y-3 overflow-y-auto p-4 relative z-10">
                  {Object.entries(results_summary).map(([key, item], index) => (
                    <div key={key} className="performance-item rounded-md border p-3 relative overflow-hidden group hover:shadow-md transition-shadow duration-300">
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent to-blue-50/50 dark:to-blue-900/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="flex items-center justify-between relative z-10">
                        <div className="flex items-center">
                          <BookOpenCheck className="me-2 h-5 w-5 text-muted-foreground rtl:me-0 rtl:ms-2" />
                          <span className="font-medium">{item.name}</span>
                        </div>
                        <Badge
                          variant={
                            item.score >= 70
                              ? "default"
                              : item.score >= 50
                              ? "secondary"
                              : "destructive"
                          }
                          className="relative overflow-hidden"
                        >
                          <span className="relative z-10">{item.score.toFixed(0)}%</span>
                          {item.score >= 90 && (
                            <div className="absolute inset-0 bg-gradient-to-r from-yellow-400/20 to-orange-400/20"></div>
                          )}
                        </Badge>
                      </div>
                      <div className="mt-1 flex justify-between text-sm text-muted-foreground relative z-10">
                        <span>
                          {t("correct")}: {item.correct}/{item.total}
                        </span>
                        {/* Progress bar */}
                        <div className="flex-1 mx-3">
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-primary rounded-full transition-all duration-1000 ease-out"
                              style={{ 
                                width: `${item.score}%`,
                                background: item.score >= 70 
                                  ? 'linear-gradient(90deg, #22c55e, #16a34a)' 
                                  : item.score >= 50 
                                  ? 'linear-gradient(90deg, #eab308, #ca8a04)'
                                  : 'linear-gradient(90deg, #ef4444, #dc2626)'
                              }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Enhanced Smart Analysis Section */}
          {smart_analysis && (
            <Alert
              ref={analysisRef}
              className="mt-6 relative overflow-hidden"
              variant={
                AdviceIconComponent === AlertTriangle
                  ? "destructive"
                  : "default"
              }
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400/5 to-indigo-500/5"></div>
              <AdviceIconComponent className="me-3 mt-1 h-5 w-5 flex-shrink-0 rtl:me-0 rtl:ms-3 relative z-10" />
              <div className="relative z-10">
                <AlertTitle className="mb-1 font-semibold flex items-center gap-2">
                  {t("smartAnalysisTitle")}
                  <Sparkles className="h-4 w-4 text-blue-500" />
                </AlertTitle>
                <AlertDescription className="text-base">
                  {smart_analysis}
                </AlertDescription>
              </div>
            </Alert>
          )}
        </CardContent>

        <CardFooter ref={footerRef} className="flex flex-col-reverse justify-center gap-3 pt-8 sm:flex-row sm:gap-4">
          <Button
            asChild
            variant="outline"
            size="lg"
            className="w-full sm:w-auto group relative overflow-hidden"
            onMouseEnter={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1.05,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
            onMouseLeave={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
          >
            <Link href={PATHS.STUDY.TRADITIONAL_LEARNING.LIST}>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-indigo-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <ListTree className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2 relative z-10 group-hover:rotate-12 transition-transform duration-300" />
              <span className="relative z-10">{t("backToOverview")}</span>
            </Link>
          </Button>
          <Button
            asChild
            variant="secondary"
            size="lg"
            className="w-full sm:w-auto group relative overflow-hidden"
            onMouseEnter={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1.05,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
            onMouseLeave={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
          >
            <Link href={PATHS.STUDY.TRADITIONAL_LEARNING.LIST}>
              <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 to-emerald-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <PlusCircle className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2 relative z-10 group-hover:rotate-90 transition-transform duration-300" />
              <span className="relative z-10">{t("startNewSession")}</span>
            </Link>
          </Button>
          <Button
            asChild
            variant="default"
            size="lg"
            className="w-full sm:w-auto group relative overflow-hidden"
            onMouseEnter={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1.05,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
            onMouseLeave={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
          >
            <Link href={PATHS.STUDY.TRADITIONAL_LEARNING.REVIEW(attemptId)}>
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <FileText className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2 relative z-10 group-hover:scale-110 transition-transform duration-300" />
              <span className="relative z-10">{t("reviewSession")}</span>
            </Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

const ScorePageSkeleton = () => {
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-4xl">
        <CardHeader className="text-center">
          <Skeleton className="mx-auto mb-4 h-8 w-3/5" />
          <Skeleton className="mx-auto h-16 w-36 rounded-full" />
        </CardHeader>
        <CardContent className="space-y-8 pt-6">
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Card key={`gamify-skel-${i}`} className="p-4">
                <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                <Skeleton className="mx-auto h-6 w-1/2" />
              </Card>
            ))}
          </div>
          <Skeleton className="h-px w-full" />
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Card key={`core-skel-${i}`} className="p-4">
                <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                <Skeleton className="mx-auto h-6 w-1/2" />
              </Card>
            ))}
          </div>
          <div>
            <Skeleton className="mx-auto mb-4 h-6 w-1/3" />
            <Skeleton className="h-64 w-full rounded-md" />
          </div>
          <Skeleton className="h-20 w-full rounded-md" />
        </CardContent>
        <CardFooter className="flex flex-col-reverse justify-center gap-3 pt-8 sm:flex-row sm:gap-4">
          <Skeleton className="h-12 w-full sm:w-40" />
          <Skeleton className="h-12 w-full sm:w-40" />
          <Skeleton className="h-12 w-full sm:w-40" />
        </CardFooter>
      </Card>
    </div>
  );
};

export default TraditionalLearningScorePage;
