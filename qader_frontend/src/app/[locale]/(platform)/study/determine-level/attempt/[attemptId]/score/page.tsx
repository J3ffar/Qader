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
import { Skeleton } from "@/components/ui/skeleton";
import ScorePieChart from "@/components/features/study/determine-level/ScorePieChart";

import {
  getTestAttemptReview,
  retakeTestAttempt,
} from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import { UserTestAttemptReview } from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

// Helper to determine qualitative level info from percentage
interface QualitativeLevelInfo {
  text: string;
  colorClass: string;
  IconComponent: React.ElementType;
}

const getQualitativeLevelInfo = (
  percentage: number | null | undefined,
  tLevel: any // Translations for "Excellent", "Good" etc.
): QualitativeLevelInfo => {
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
    staleTime: 5 * 60 * 1000,
  });

  const retakeMutation = useMutation({
    mutationFn: () => retakeTestAttempt(attemptId),
    onSuccess: (data) => {
      toast.success(t("api.retakeSuccess"));
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

  if (isLoading) return <ScorePageSkeleton />;

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

  const overallScore = reviewData.score_percentage;
  const verbalScore = reviewData.score_verbal;
  const quantitativeScore = reviewData.score_quantitative;
  const timeTakenMinutes = reviewData.results_summary?.time_taken_minutes;
  const levelInfo = getQualitativeLevelInfo(overallScore, tLevel);

  const totalQuestions = reviewData.questions.length;
  const correctAnswers = reviewData.questions.filter(
    (q) => q.user_is_correct === true
  ).length;
  const incorrectAnswers = reviewData.questions.filter(
    (q) => q.user_is_correct === false
  ).length;
  // Assuming user_answer is null if skipped, and not an empty string.
  const answeredQuestionsCount = reviewData.questions.filter(
    (q) => q.user_answer !== null
  ).length;
  const skippedAnswers = totalQuestions - answeredQuestionsCount;

  let adviceText =
    reviewData.results_summary?.smart_analysis || t("adviceDefault");
  let AdviceIconComponent: React.ElementType = Info;
  let adviceAlertVariant: "default" | "destructive" = "default";

  // This logic for advice generation if smart_analysis is missing is from original code
  if (
    !reviewData.results_summary?.smart_analysis &&
    overallScore !== null &&
    overallScore !== undefined
  ) {
    if (
      verbalScore !== null &&
      quantitativeScore !== null &&
      verbalScore < quantitativeScore &&
      verbalScore < 70
    ) {
      adviceText = t("adviceReviewVerbal");
    } else if (
      quantitativeScore !== null &&
      verbalScore !== null &&
      quantitativeScore < verbalScore &&
      quantitativeScore < 70
    ) {
      adviceText = t("adviceReviewQuantitative");
    }
  }

  if (adviceText) {
    if (adviceText === t("adviceDefault")) {
      AdviceIconComponent = Info;
    } else if (
      adviceText === t("adviceReviewVerbal") ||
      adviceText === t("adviceReviewQuantitative")
    ) {
      AdviceIconComponent = AlertTriangle; // Warning/Needs attention
      // adviceAlertVariant could be 'destructive' if we want to strongly highlight it,
      // but 'default' with a warning icon is less alarming.
    } else if (
      reviewData.results_summary?.smart_analysis &&
      adviceText === reviewData.results_summary.smart_analysis
    ) {
      AdviceIconComponent = ThumbsUp; // Positive or constructive feedback
    }
    // Fallback to Info icon if not matched
  }

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-4xl shadow-xl">
        {" "}
        {/* Increased max-width for more content */}
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

          {(verbalScore !== null || quantitativeScore !== null) &&
            totalQuestions > 0 && (
              <div className="mt-8">
                <h3 className="mb-4 text-center text-xl font-semibold">
                  {t("scoreDistribution")}
                </h3>
                <ScorePieChart
                  verbalScore={verbalScore}
                  quantitativeScore={quantitativeScore}
                />
              </div>
            )}

          {adviceText && (
            <Alert variant={adviceAlertVariant} className="mt-6">
              <div className="flex items-center text-center md:text-start">
                <AdviceIconComponent className="me-3 h-5 w-5 flex-shrink-0 rtl:me-0 rtl:ms-3" />
                <AlertDescription className="text-base">
                  {adviceText}
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
            variant="secondary" // Changed from outline to secondary for variety
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

// Renamed original Skeleton to be more specific and updated its structure
const ScorePageSkeleton = () => {
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-4xl">
        <CardHeader className="text-center">
          <Skeleton className="mx-auto mb-4 h-8 w-3/5" /> {/* Title */}
          <Skeleton className="mx-auto h-12 w-32 rounded-full" />{" "}
          {/* Score badge */}
        </CardHeader>
        <CardContent className="space-y-8 pt-6">
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map(
              (
                _,
                i // Skeleton for 4 stat cards
              ) => (
                <Card key={i} className="p-4">
                  <Skeleton className="mx-auto mb-2 h-8 w-8 rounded-full" />
                  <Skeleton className="mx-auto mb-1 h-4 w-3/4" />
                  <Skeleton className="mx-auto h-6 w-1/2" />
                </Card>
              )
            )}
          </div>
          <div>
            <Skeleton className="mx-auto mb-4 h-6 w-1/3" /> {/* Chart title */}
            <Skeleton className="h-64 w-full rounded-md" />{" "}
            {/* Chart placeholder */}
          </div>
          <Skeleton className="h-12 w-full rounded-md" />{" "}
          {/* Advice placeholder */}
        </CardContent>
        <CardFooter className="flex flex-col-reverse justify-center gap-3 pt-8 sm:flex-row sm:gap-4">
          <Skeleton className="h-12 w-full sm:w-40" /> {/* Back to overview */}
          <Skeleton className="h-12 w-full sm:w-36" /> {/* Retake */}
          <Skeleton className="h-12 w-full sm:w-40" /> {/* Review */}
        </CardFooter>
      </Card>
    </div>
  );
};

export default LevelAssessmentScorePage;
