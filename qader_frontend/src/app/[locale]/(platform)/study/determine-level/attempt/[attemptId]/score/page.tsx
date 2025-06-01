"use client";

import React from "react";
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
  Award, // For Badges
  Sparkles, // For Points
  Flame, // For Streak
  Target, // For performance breakdown
  BookOpenCheck, // For sub-skill details
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
import { Badge } from "@/components/ui/badge"; // Shadcn Badge
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import ScorePieChart from "@/components/features/platform/study/determine-level/ScorePieChart";

import {
  getTestAttemptReview,
  retakeTestAttempt,
} from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import {
  UserTestAttemptReview,
  BadgeWon,
  ResultsSummaryItem,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

// Helper to determine qualitative level info from percentage (remains largely the same)
interface QualitativeLevelInfo {
  text: string;
  colorClass: string;
  IconComponent: React.ElementType;
}

const getQualitativeLevelInfo = (
  percentage: number | null | undefined,
  tLevel: any
): QualitativeLevelInfo => {
  // ... (implementation remains the same as provided)
  const defaultLevel = {
    text: tLevel("notAvailable"),
    colorClass: "text-muted-foreground",
    IconComponent: HelpCircle,
  };
  if (percentage === null || percentage === undefined) return defaultLevel;

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

  const {
    data: reviewData,
    isLoading,
    error,
  } = useQuery<UserTestAttemptReview, Error, UserTestAttemptReview, string[]>({
    queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_REVIEW, attemptId],
    queryFn: () => getTestAttemptReview(attemptId),
    enabled: !!attemptId,
    staleTime: 1 * 60 * 1000, // Reduced stale time as score page is usually viewed once right after
    refetchOnWindowFocus: false, // Usually score doesn't change
  });

  const retakeMutation = useMutation({
    mutationFn: () => retakeTestAttempt(attemptId),
    onSuccess: (data) => {
      toast.success(
        t("api.retakeSuccessNewTest", { attemptId: data.attempt_id })
      );
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPTS],
      });
      // NProgress will handle visual loading bar for this navigation
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

  if (isLoading) return <ScorePageSkeletonV2 />; // Use updated skeleton

  if (error || !reviewData) {
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

  // Prioritize nested score object if available, otherwise use flat scores
  const overallScore = reviewData.score?.overall ?? reviewData.score_percentage;
  const verbalScore = reviewData.score?.verbal ?? reviewData.score_verbal;
  const quantitativeScore =
    reviewData.score?.quantitative ?? reviewData.score_quantitative;

  const timeTakenMinutes = reviewData.time_taken_minutes; // Assuming this remains available
  const levelInfo = getQualitativeLevelInfo(overallScore, tLevel);

  const totalQuestions =
    reviewData.total_questions_api ?? reviewData.questions.length;
  const correctAnswers =
    reviewData.correct_answers_in_test_count ??
    reviewData.questions.filter((q) => q.user_is_correct === true).length;

  // Calculate incorrect and skipped based on fetched questions if specific counts aren't available directly for these two
  const answeredQuestionsCount =
    reviewData.answered_question_count ??
    reviewData.questions.filter((q) => q.user_selected_choice !== null).length;
  const incorrectAnswers = reviewData.questions.filter(
    (q) => q.user_is_correct === false
  ).length; // This might be different from (total - correct - skipped) if API counts unattempted as incorrect
  const skippedAnswers = totalQuestions - answeredQuestionsCount;

  const smartAnalysis = reviewData.smart_analysis || t("adviceDefault");
  let AdviceIconComponent: React.ElementType = ThumbsUp;
  if (reviewData.smart_analysis) {
    if (overallScore !== null && overallScore < 50)
      AdviceIconComponent = AlertTriangle;
    else AdviceIconComponent = ThumbsUp;
  } else if (
    !reviewData.smart_analysis &&
    overallScore !== null &&
    overallScore < 70
  ) {
    AdviceIconComponent = Info; // Default advice is more like info
  }

  const totalPointsEarned =
    (reviewData.points_from_test_completion_event ?? 0) +
    (reviewData.points_from_correct_answers_this_test ?? 0);

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-4xl shadow-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold md:text-3xl">
            {t("yourScoreIsReady")}
          </CardTitle>
          {overallScore !== null && overallScore !== undefined ? (
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
          {/* Gamification Stats Row */}
          {(totalPointsEarned > 0 ||
            reviewData.badges_won?.length ||
            reviewData.streak_info) && (
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
              {reviewData.streak_info && (
                <Card className="p-4">
                  <Flame className="mx-auto mb-2 h-8 w-8 text-orange-500" />
                  <p className="text-sm text-muted-foreground">
                    {t("currentStreak")}
                  </p>
                  <p className="text-xl font-bold">
                    {reviewData.streak_info.current_days} {t("days")}
                    {reviewData.streak_info.updated && (
                      <CheckCircle className="ms-1 inline-block h-5 w-5 text-green-500" />
                    )}
                  </p>
                </Card>
              )}
              {reviewData.badges_won && reviewData.badges_won.length > 0 && (
                <Card className="p-4 sm:col-span-2 lg:col-span-1">
                  {" "}
                  {/* Adjust span for badges */}
                  <Award className="mx-auto mb-2 h-8 w-8 text-indigo-500" />
                  <p className="text-sm text-muted-foreground">
                    {t("badgesUnlocked")}
                  </p>
                  <div className="mt-1 flex flex-wrap justify-center gap-2">
                    {reviewData.badges_won.map((badge) => (
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
          )}
          {(totalPointsEarned > 0 ||
            reviewData.badges_won?.length ||
            reviewData.streak_info) && <Separator />}

          {/* Core Test Stats Row */}
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-4">
            <Card className="p-4">
              <Clock className="mx-auto mb-2 h-8 w-8 text-primary" />
              <p className="text-sm text-muted-foreground">{t("timeTaken")}</p>
              {timeTakenMinutes !== null && timeTakenMinutes !== undefined ? (
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

          {/* Score Distribution Pie Chart & Detailed Breakdown */}
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

            {reviewData.results_summary &&
              Object.keys(reviewData.results_summary).length > 0 && (
                <div>
                  <h3 className="mb-4 text-center text-xl font-semibold">
                    <Target className="me-2 inline-block h-6 w-6 rtl:me-0 rtl:ms-2" />
                    {t("detailedPerformance")}
                  </h3>
                  <Card>
                    <CardContent className="max-h-80 space-y-3 overflow-y-auto p-4">
                      {Object.entries(reviewData.results_summary).map(
                        ([key, item]) => (
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
                        )
                      )}
                    </CardContent>
                  </Card>
                </div>
              )}
          </div>

          {smartAnalysis && (
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
                  {smartAnalysis}
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
            {retakeMutation.isPending && (
              <Loader2 className="me-2 h-5 w-5 animate-spin rtl:me-0 rtl:ms-2" />
            )}
            <RefreshCcw className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
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

// Use this for the loading.tsx file as well
const ScorePageSkeletonV2 = () => {
  // Renamed to V2
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-4xl">
        <CardHeader className="text-center">
          <Skeleton className="mx-auto mb-4 h-8 w-3/5" /> {/* Title */}
          <Skeleton className="mx-auto h-16 w-36 rounded-full" />{" "}
          {/* Score badge */}
        </CardHeader>
        <CardContent className="space-y-8 pt-6">
          {/* Skeletons for Gamification Stats */}
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Card key={`gamify-skel-${i}`} className="p-4">
                <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                <Skeleton className="mx-auto h-6 w-1/2" />
              </Card>
            ))}
          </div>
          <Skeleton className="h-px w-full" /> {/* Separator Skeleton */}
          {/* Skeletons for Core Test Stats */}
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={`core-skel-${i}`} className="p-4">
                <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                <Skeleton className="mx-auto h-6 w-1/2" />
              </Card>
            ))}
          </div>
          {/* Skeletons for Score Distribution & Detailed Performance */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <Skeleton className="mx-auto mb-4 h-6 w-1/3" />{" "}
              {/* Chart/Detail title */}
              <Skeleton className="h-64 w-full rounded-md" />{" "}
              {/* Chart/Detail placeholder */}
            </div>
            <div>
              <Skeleton className="mx-auto mb-4 h-6 w-1/3" />{" "}
              {/* Chart/Detail title */}
              <Skeleton className="h-64 w-full rounded-md" />{" "}
              {/* Chart/Detail placeholder */}
            </div>
          </div>
          {/* Skeleton for Smart Analysis */}
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
