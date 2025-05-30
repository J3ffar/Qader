"use client";

import React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import {
  AlertTriangle,
  BadgeCheck,
  Clock,
  FileText,
  Loader2,
  RefreshCcw,
  ArrowLeft,
  ArrowRight,
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

// Helper to determine qualitative level from percentage
const getQualitativeLevel = (
  percentage: number | null | undefined,
  tBadge: any
): string => {
  if (percentage === null || percentage === undefined) return tBadge("default");
  if (percentage >= 90) return tBadge("excellent");
  if (percentage >= 80) return tBadge("veryGood");
  if (percentage >= 70) return tBadge("good");
  if (percentage >= 50) return tBadge("acceptable"); // Added acceptable
  return tBadge("weak");
};

const LevelAssessmentScorePage = () => {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const t = useTranslations("Study.determineLevel.score");
  const tBadge = useTranslations("Study.determineLevel.badgeColors");
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
    staleTime: 5 * 60 * 1000, // Scores don't change often for a completed attempt
  });

  const retakeMutation = useMutation({
    mutationFn: () => retakeTestAttempt(attemptId),
    onSuccess: (data) => {
      toast.success(t("api.retakeSuccess"));
      // Invalidate list to show new "started" attempt if API updates it.
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPTS],
      });
      // Navigate to the new attempt
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
          <AlertTriangle className="mx-auto mb-2 h-5 w-5" />
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
            <ArrowRight className="me-2 h-4 w-4" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4" />
          )}
          {tCommon("backToList")}
        </Button>
      </div>
    );
  }

  // Extract data - API might put these in reviewData.results_summary or directly
  const overallScore = reviewData.score_percentage;
  const verbalScore = reviewData.score_verbal;
  const quantitativeScore = reviewData.score_quantitative;

  // These might need to be derived or come from results_summary
  const timeTakenMinutes = reviewData.results_summary?.time_taken_minutes || 20; // Default or calculate
  const currentLevelDisplay = getQualitativeLevel(overallScore, tBadge); // Use helper

  let advice = reviewData.results_summary?.smart_analysis || t("adviceDefault");
  if (!advice && overallScore !== null && overallScore !== undefined) {
    if (
      verbalScore !== null &&
      quantitativeScore !== null &&
      verbalScore < quantitativeScore &&
      verbalScore < 70
    ) {
      advice = t("adviceReviewVerbal");
    } else if (
      quantitativeScore !== null &&
      verbalScore !== null &&
      quantitativeScore < verbalScore &&
      quantitativeScore < 70
    ) {
      advice = t("adviceReviewQuantitative");
    }
  }

  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-3xl shadow-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">
            {t("yourScoreIsReady")}
          </CardTitle>
          {overallScore !== null && overallScore !== undefined && (
            <div className="mt-4">
              <span className="rounded-full bg-primary px-6 py-2 text-xl font-bold text-primary-foreground">
                {overallScore.toFixed(0)}/100
              </span>
            </div>
          )}
        </CardHeader>

        <CardContent className="space-y-8">
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2">
            <Card className="p-4">
              <Clock className="mx-auto mb-2 h-7 w-7 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">{t("timeTaken")}</p>
              <p className="text-lg font-bold text-primary">
                {timeTakenMinutes} {t("minutes")}
              </p>
            </Card>
            <Card className="p-4">
              <BadgeCheck className="mx-auto mb-2 h-7 w-7 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {t("currentLevel")}
              </p>
              <p className="text-lg font-bold text-yellow-500">
                {currentLevelDisplay}
              </p>
            </Card>
          </div>

          {(verbalScore !== null || quantitativeScore !== null) && (
            <div className="mt-6">
              <h3 className="mb-4 text-center text-xl font-semibold">
                {t("scoreDistribution")}
              </h3>
              <ScorePieChart
                verbalScore={verbalScore}
                quantitativeScore={quantitativeScore}
              />
            </div>
          )}

          {advice && (
            <Alert
              variant={
                advice === t("adviceDefault") ? "default" : "destructive"
              }
              className="text-center"
            >
              <AlertTriangle className="me-1 inline h-4 w-4" />
              <AlertDescription>{advice}</AlertDescription>
            </Alert>
          )}
        </CardContent>

        <CardFooter className="flex flex-col justify-center gap-4 pt-8 sm:flex-row">
          <Button asChild variant="default" size="lg">
            <Link href={PATHS.STUDY.DETERMINE_LEVEL.REVIEW(attemptId)}>
              <FileText className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />{" "}
              {tCommon("reviewTest")}
            </Link>
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={handleRetakeTest}
            disabled={retakeMutation.isPending}
          >
            {retakeMutation.isPending && (
              <Loader2 className="me-2 h-5 w-5 animate-spin rtl:me-0 rtl:ms-2" />
            )}
            <RefreshCcw className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />{" "}
            {t("retakeTest")}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

const ScorePageSkeleton = () => {
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <Card className="mx-auto max-w-3xl">
        <CardHeader className="text-center">
          <Skeleton className="mx-auto mb-4 h-8 w-3/5" /> {/* Title */}
          <Skeleton className="mx-auto h-10 w-28 rounded-full" />{" "}
          {/* Score badge */}
        </CardHeader>
        <CardContent className="space-y-8">
          <div className="grid grid-cols-1 gap-4 text-center sm:grid-cols-2">
            <Card className="p-4">
              <Skeleton className="mx-auto mb-2 h-7 w-7 rounded-full" />
              <Skeleton className="mx-auto mb-1 h-4 w-20" />
              <Skeleton className="mx-auto h-6 w-16" />
            </Card>
            <Card className="p-4">
              <Skeleton className="mx-auto mb-2 h-7 w-7 rounded-full" />
              <Skeleton className="mx-auto mb-1 h-4 w-24" />
              <Skeleton className="mx-auto h-6 w-12" />
            </Card>
          </div>
          <div>
            <Skeleton className="mx-auto mb-4 h-6 w-1/3" /> {/* Chart title */}
            <Skeleton className="h-64 w-full rounded-md" />{" "}
            {/* Chart placeholder */}
          </div>
          <Skeleton className="h-10 w-full rounded-md" />{" "}
          {/* Advice placeholder */}
        </CardContent>
        <CardFooter className="flex flex-col justify-center gap-4 pt-8 sm:flex-row">
          <Skeleton className="h-12 w-36" />
          <Skeleton className="h-12 w-36" />
        </CardFooter>
      </Card>
    </div>
  );
};

export default LevelAssessmentScorePage;
