"use client";

import React, { useMemo, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import {
  AlertTriangle,
  Clock,
  FileText,
  Loader2,
  RefreshCcw,
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  XCircle,
  HelpCircle,
  BarChart3,
  ThumbsUp,
  Info,
  ListTree,
  TrendingUp,
  Award,
  Sparkles,
  Flame,
  Target,
  BookOpenCheck,
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
import ScorePieChart from "@/components/features/platform/study/determine-level/ScorePieChart";
import { useAuthActions, useAuthStore } from "@/store/auth.store";
import { UserProfile } from "@/types/api/auth.types";

import {
  getTestAttemptReview,
  retakeTestAttempt,
} from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import {
  UserTestAttemptCompletionResponse,
  UserTestAttemptReviewResponse,
  UserTestAttemptStartResponse,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

interface QualitativeLevelInfo {
  text: string;
  colorClass: string;
  IconComponent: React.ElementType;
}

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
      IconComponent: TrendingUp,
    };
  if (percentage >= 80)
    return {
      text: tLevel("veryGood"),
      colorClass: "text-sky-600 dark:text-sky-500",
      IconComponent: TrendingUp,
    };
  if (percentage >= 70)
    return {
      text: tLevel("good"),
      colorClass: "text-blue-600 dark:text-blue-500",
      IconComponent: CheckCircle,
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

const LevelAssessmentScorePage = () => {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const t = useTranslations("Study.determineLevel.score");
  const tLevel = useTranslations("Study.determineLevel.badgeColors");
  const tCommon = useTranslations("Common");
  const locale = params.locale as string;

  const attemptId = params.attemptId as string;

  // Get auth state and actions for updating global user profile ---
  const { user } = useAuthStore();
  const { updateUserProfile } = useAuthActions();
  const hasUpdatedProfileRef = useRef(false);

  const completionData =
    queryClient.getQueryData<UserTestAttemptCompletionResponse>([
      QUERY_KEYS.USER_TEST_ATTEMPT_COMPLETION_RESULT,
      attemptId,
    ]);

  const {
    data: reviewData,
    isLoading: isLoadingReview,
    error,
  } = useQuery<UserTestAttemptReviewResponse, Error>({
    queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_REVIEW, attemptId],
    queryFn: () => getTestAttemptReview(attemptId),
    enabled: !!attemptId && !completionData,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (completionData && user && !hasUpdatedProfileRef.current) {
      const totalPointsEarned =
        (completionData.points_from_test_completion_event ?? 0) +
        (completionData.points_from_correct_answers_this_test ?? 0);

      const newStreakDays = completionData.streak_info?.current_days;

      const profileUpdates: Partial<UserProfile> = {};
      let hasGamificationUpdate = false;

      if (totalPointsEarned > 0) {
        profileUpdates.points = user.points + totalPointsEarned;
        hasGamificationUpdate = true;
      }

      if (
        newStreakDays !== undefined &&
        newStreakDays !== user.current_streak_days
      ) {
        profileUpdates.current_streak_days = newStreakDays;
        hasGamificationUpdate = true;
      }

      if (user.level_determined === false) {
        profileUpdates.level_determined = true;
      }

      if (Object.keys(profileUpdates).length > 0) {
        // 1. Update the global client-side state for immediate UI feedback in the header
        updateUserProfile(profileUpdates);
        hasUpdatedProfileRef.current = true;

        // 2. --- NEW: Invalidate server-state caches ---
        // If points or streak were updated, the data for their dropdowns is now stale.
        if (hasGamificationUpdate) {
          console.log("Invalidating gamification query caches...");
          // Invalidate the weekly points summary so the dropdown refetches
          queryClient.invalidateQueries({
            queryKey: [QUERY_KEYS.WEEKLY_POINTS_SUMMARY],
          });
          // Invalidate the study days log for the streak dropdown
          queryClient.invalidateQueries({
            queryKey: [QUERY_KEYS.STUDY_DAYS_LOG],
          });
        }
      }
    }
  }, [completionData, user, updateUserProfile, t, queryClient]);

  const isLoading = isLoadingReview && !completionData;
  const combinedData = completionData || reviewData;

  const retakeMutation = useMutation<UserTestAttemptStartResponse, Error>({
    mutationFn: () => retakeTestAttempt(attemptId),
    onSuccess: (data) => {
      toast.success(
        t("api.retakeSuccessNewTest", { attemptId: data.attempt_id })
      );
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPTS],
      });
      router.push(PATHS.STUDY.DETERMINE_LEVEL.ATTEMPT(data.attempt_id));
    },
    onError: (err: any) => {
      const errorMsg = getApiErrorMessage(err, tCommon("errors.generic"));
      toast.error(t("api.retakeError", { error: errorMsg }));
    },
  });

  const handleRetakeTest = () => {
    retakeMutation.mutate();
  };

  const displayData = useMemo(() => {
    if (!combinedData) return null;

    if ("score" in combinedData && combinedData.score) {
      const data = combinedData as UserTestAttemptCompletionResponse;
      const answeredCount = data.answered_question_count;
      const correctCount = data.correct_answers_in_test_count;
      return {
        isFallback: false,
        overallScore: data.score.overall,
        verbalScore: data.score.verbal,
        quantitativeScore: data.score.quantitative,
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

    const data = combinedData as UserTestAttemptReviewResponse;
    const totalQuestions = data.questions.length;
    const answeredCount = data.questions.filter(
      (q) => q.user_answer_details?.selected_choice !== null
    ).length;
    const correctCount = data.questions.filter(
      (q) => q.user_answer_details?.is_correct === true
    ).length;

    return {
      isFallback: true,
      overallScore: data.score_percentage,
      verbalScore: data.score_verbal,
      quantitativeScore: data.score_quantitative,
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
        <Button
          onClick={() => router.push(PATHS.STUDY.DETERMINE_LEVEL.LIST)}
          variant="outline"
          className="mt-6"
        >
          {locale === "ar" ? (
            <ArrowRight className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
          )}
          {t("backToOverview")}
        </Button>
      </div>
    );
  }

  const {
    overallScore,
    verbalScore,
    quantitativeScore,
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

  let AdviceIconComponent: React.ElementType = ThumbsUp;
  if (smart_analysis && overallScore !== null && overallScore < 50) {
    AdviceIconComponent = AlertTriangle;
  }

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-4xl shadow-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold md:text-3xl">
            {t("yourScoreIsReady")}
          </CardTitle>
          {overallScore !== null ? (
            <div className="mt-4">
              <span
                className={`inline-flex items-center rounded-full bg-primary px-6 py-3 text-3xl font-bold text-primary-foreground shadow-lg`}
              >
                {overallScore.toFixed(0)}
                <span className="ms-1 text-xl opacity-80">/100</span>
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
          {(totalPointsEarned > 0 ||
            (badges_won && badges_won.length > 0) ||
            streak_info) && (
            <>
              <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-3">
                {totalPointsEarned > 0 && (
                  <Card className="p-4">
                    <Sparkles className="mx-auto mb-2 h-8 w-8 text-yellow-500" />
                    <p className="text-sm text-muted-foreground">
                      {t("pointsEarned")}
                    </p>
                    <p className="text-xl font-bold">{totalPointsEarned}</p>
                  </Card>
                )}
                {streak_info && (
                  <Card className="p-4">
                    <Flame className="mx-auto mb-2 h-8 w-8 text-orange-500" />
                    <p className="text-sm text-muted-foreground">
                      {t("currentStreak")}
                    </p>
                    <p className="text-xl font-bold">
                      {streak_info.current_days} {t("days")}
                      {streak_info.updated && (
                        <CheckCircle className="ms-1 inline-block h-5 w-5 text-green-500" />
                      )}
                    </p>
                  </Card>
                )}
                {badges_won && badges_won.length > 0 && (
                  <Card className="p-4 sm:col-span-2 lg:col-span-1">
                    <Award className="mx-auto mb-2 h-8 w-8 text-indigo-500" />
                    <p className="text-sm text-muted-foreground">
                      {t("badgesUnlocked")}
                    </p>
                    <div className="mt-1 flex flex-wrap justify-center gap-2">
                      {badges_won.map((badge) => (
                        <Badge
                          key={badge.slug}
                          variant="secondary"
                          className="text-xs"
                          title={badge.description}
                        >
                          {badge.name}
                        </Badge>
                      ))}
                    </div>
                  </Card>
                )}
              </div>
              <Separator />
            </>
          )}

          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-4">
            <Card className="p-4">
              <Clock className="mx-auto mb-2 h-8 w-8 text-primary" />
              <p className="text-sm text-muted-foreground">{t("timeTaken")}</p>
              {timeTakenMinutes !== null ? (
                <p className="text-xl font-bold">
                  {timeTakenMinutes} {t("minutes")}
                </p>
              ) : (
                <p className="text-lg font-semibold text-muted-foreground">
                  {tCommon("status.notAvailableShort")}
                </p>
              )}
            </Card>
            <Card className="p-4">
              <levelInfo.IconComponent
                className={`mx-auto mb-2 h-8 w-8 ${levelInfo.colorClass}`}
              />
              <p className="text-sm text-muted-foreground">
                {t("currentLevel")}
              </p>
              <p className={`text-xl font-bold ${levelInfo.colorClass}`}>
                {levelInfo.text}
              </p>
            </Card>
            <Card className="p-4">
              <CheckCircle className="mx-auto mb-2 h-8 w-8 text-green-500" />
              <p className="text-sm text-muted-foreground">
                {t("correctAnswers")}
              </p>
              <p className="text-xl font-bold">
                {correctAnswers}{" "}
                <span className="text-base text-muted-foreground">
                  /{totalQuestions || tCommon("status.notAvailableShort")}
                </span>
              </p>
            </Card>
            <Card className="p-4">
              <XCircle className="mx-auto mb-2 h-8 w-8 text-red-500" />
              <p className="text-sm text-muted-foreground">
                {t("incorrectAnswers")}
              </p>
              <p className="text-xl font-bold">
                {incorrectAnswers}
                {skippedAnswers > 0 && (
                  <span className="ms-2 text-sm font-normal text-muted-foreground">
                    (+{skippedAnswers} {t("skipped")})
                  </span>
                )}
              </p>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {(verbalScore !== null || quantitativeScore !== null) &&
              totalQuestions > 0 && (
                <div dir="ltr">
                  <h3 className="mb-4 text-center text-xl font-semibold">
                    <BarChart3 className="me-2 inline-block h-6 w-6 rtl:me-0 rtl:ms-2" />
                    {t("scoreDistribution")}
                  </h3>
                  <ScorePieChart
                    verbalScore={verbalScore}
                    quantitativeScore={quantitativeScore}
                  />
                </div>
              )}

            {results_summary && Object.keys(results_summary).length > 0 && (
              <div>
                <h3 className="mb-4 text-center text-xl font-semibold">
                  <Target className="me-2 inline-block h-6 w-6 rtl:me-0 rtl:ms-2" />
                  {t("detailedPerformance")}
                </h3>
                <Card>
                  <CardContent className="max-h-80 space-y-3 overflow-y-auto p-4">
                    {Object.entries(results_summary).map(([key, item]) => (
                      <div key={key} className="rounded-md border p-3">
                        <div className="flex items-center justify-between">
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
                          >
                            {item.score.toFixed(0)}%
                          </Badge>
                        </div>
                        <div className="mt-1 flex justify-between text-sm text-muted-foreground">
                          <span>
                            {t("correct")}: {item.correct}/{item.total}
                          </span>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {smart_analysis && (
            <Alert
              className="mt-6"
              variant={
                AdviceIconComponent === AlertTriangle
                  ? "destructive"
                  : "default"
              }
            >
              <AdviceIconComponent className="me-3 mt-1 h-5 w-5 flex-shrink-0 rtl:me-0 rtl:ms-3" />
              <div>
                <AlertTitle className="mb-1 font-semibold">
                  {t("smartAnalysisTitle")}
                </AlertTitle>
                <AlertDescription className="text-base">
                  {smart_analysis}
                </AlertDescription>
              </div>
            </Alert>
          )}
        </CardContent>

        <CardFooter className="flex flex-col-reverse justify-center gap-3 pt-8 sm:flex-row sm:gap-4">
          <Button
            asChild
            variant="outline"
            size="lg"
            className="w-full sm:w-auto"
          >
            <Link href={PATHS.STUDY.DETERMINE_LEVEL.LIST}>
              <ListTree className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
              {t("backToOverview")}
            </Link>
          </Button>
          <Button
            variant="secondary"
            size="lg"
            onClick={handleRetakeTest}
            disabled={retakeMutation.isPending}
            className="w-full sm:w-auto"
          >
            {retakeMutation.isPending ? (
              <Loader2 className="me-2 h-5 w-5 animate-spin rtl:me-0 rtl:ms-2" />
            ) : (
              <RefreshCcw className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
            )}
            {t("retakeTest")}
          </Button>
          <Button
            asChild
            variant="default"
            size="lg"
            className="w-full sm:w-auto"
          >
            <Link href={PATHS.STUDY.DETERMINE_LEVEL.REVIEW(attemptId)}>
              <FileText className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
              {tCommon("reviewTest")}
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
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={`core-skel-${i}`} className="p-4">
                <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                <Skeleton className="mx-auto h-6 w-1/2" />
              </Card>
            ))}
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <Skeleton className="mx-auto mb-4 h-6 w-1/3" />
              <Skeleton className="h-64 w-full rounded-md" />
            </div>
            <div>
              <Skeleton className="mx-auto mb-4 h-6 w-1/3" />
              <Skeleton className="h-64 w-full rounded-md" />
            </div>
          </div>
          <Skeleton className="h-20 w-full rounded-md" />
        </CardContent>
        <CardFooter className="flex flex-col-reverse justify-center gap-3 pt-8 sm:flex-row sm:gap-4">
          <Skeleton className="h-12 w-full sm:w-40" />
          <Skeleton className="h-12 w-full sm:w-36" />
          <Skeleton className="h-12 w-full sm:w-40" />
        </CardFooter>
      </Card>
    </div>
  );
};

export default LevelAssessmentScorePage;
