"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import {
  ArrowLeft,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Filter as FilterIcon,
  BookOpen,
  ThumbsDown,
  HelpCircle as HelpCircleIcon,
  Loader2,
  AlertTriangle,
  Frown,
  FileText,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import ReviewQuestionCard from "@/components/features/platform/study/determine-level/ReviewQuestionCard";

import { getTestAttemptReview } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import type {
  UserTestAttemptReview,
  UserTestAttemptReviewQuestion, // For explicit typing if needed
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

type FilterType = "all" | "incorrect" | "skipped";

type TestAttemptReviewQueryKey = readonly [
  string,
  string,
  { readonly incorrect_only: boolean } // API takes string, but boolean for key consistency
];

const LevelAssessmentReviewPage = () => {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations("Study.determineLevel.review");
  const tScore = useTranslations("Study.determineLevel.score");
  const tCommon = useTranslations("Common");
  const locale = params.locale as string;
  const attemptId = params.attemptId as string;

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [filterType, setFilterType] = useState<FilterType>("all");

  const {
    data: reviewData,
    isLoading,
    error: queryError,
    isFetching, // Good for subtle loading states on re-fetch/filter change
  } = useQuery<
    UserTestAttemptReview,
    Error,
    UserTestAttemptReview,
    TestAttemptReviewQueryKey
  >({
    queryKey: [
      QUERY_KEYS.USER_TEST_ATTEMPT_REVIEW,
      attemptId,
      { incorrect_only: false }, // Fetch all initially
    ] as const,
    queryFn: () => getTestAttemptReview(attemptId, { incorrect_only: "false" }),
    enabled: !!attemptId,
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const allQuestions = useMemo(() => reviewData?.questions || [], [reviewData]);

  const incorrectQuestions = useMemo(
    () =>
      allQuestions.filter(
        (q) => q.user_selected_choice !== null && q.user_is_correct === false
      ),
    [allQuestions]
  );

  const skippedQuestions = useMemo(
    () => allQuestions.filter((q) => q.user_selected_choice === null),
    [allQuestions]
  );

  const filteredQuestions = useMemo(() => {
    switch (filterType) {
      case "incorrect":
        return incorrectQuestions;
      case "skipped":
        return skippedQuestions;
      case "all":
      default:
        return allQuestions;
    }
  }, [filterType, allQuestions, incorrectQuestions, skippedQuestions]);

  // Reset index when filter type or the underlying data changes
  useEffect(() => {
    setCurrentQuestionIndex(0);
  }, [filterType, allQuestions.length]); // Or depend on filteredQuestions directly

  const handleNextQuestion = () => {
    if (currentQuestionIndex < filteredQuestions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  const currentQuestionData = filteredQuestions[currentQuestionIndex];

  if (isLoading) {
    // Primary loading is handled by loading.tsx. This is a fallback.
    return (
      <div className="flex min-h-[calc(100vh-200px)] items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }

  if (queryError || !reviewData) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6 text-center">
        <Alert variant="destructive" className="max-w-lg">
          <AlertTriangle className="mx-auto mb-2 h-6 w-6" />
          <AlertTitle>{tCommon("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(queryError, t("errors.fetchReviewFailed"))}
          </AlertDescription>
        </Alert>
        <Button
          onClick={() =>
            router.push(PATHS.STUDY.DETERMINE_LEVEL.SCORE(attemptId))
          }
          variant="outline"
          className="mt-6"
        >
          {locale === "ar" ? (
            <ArrowRight className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
          )}
          {t("backToScorePage")}
        </Button>
      </div>
    );
  }

  const overallScore = reviewData.score?.overall ?? reviewData.score_percentage;
  const verbalScore = reviewData.score?.verbal ?? reviewData.score_verbal;
  const quantitativeScore =
    reviewData.score?.quantitative ?? reviewData.score_quantitative;

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      {/* Header Card */}
      <Card className="overflow-hidden shadow-md">
        <CardHeader className="bg-muted/20 p-4 sm:p-5">
          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() =>
                  router.push(PATHS.STUDY.DETERMINE_LEVEL.SCORE(attemptId))
                }
                aria-label={t("backToScorePage")}
                className="text-primary hover:bg-primary/10"
              >
                {locale === "ar" ? (
                  <ArrowRight className="h-5 w-5" />
                ) : (
                  <ArrowLeft className="h-5 w-5" />
                )}
              </Button>
              <h1 className="flex items-center text-xl font-semibold text-primary sm:text-2xl">
                <FileText className="me-2.5 h-[1.3em] w-[1.3em] rtl:me-0 rtl:ms-2.5" />
                {t("reviewYourAttempt")}
              </h1>
            </div>
            {overallScore !== null && overallScore !== undefined && (
              <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 rounded-lg border bg-background p-2 px-3 text-xs shadow-sm sm:text-sm">
                <div
                  className="flex items-center"
                  title={tScore("overallScore")}
                >
                  <TrendingUp className="me-1 h-4 w-4 text-primary rtl:me-0 rtl:ms-1" />
                  <span className="font-medium">
                    {overallScore.toFixed(0)}%
                  </span>
                </div>
                {verbalScore !== null && (
                  <>
                    <span className="text-muted-foreground">|</span>
                    <div
                      className="flex items-center"
                      title={tScore("verbalSection")}
                    >
                      <span className="font-medium text-yellow-600 dark:text-yellow-400">
                        {tScore("verbalSectionShort")}:
                      </span>
                      <span className="ms-1 font-medium">
                        {verbalScore.toFixed(0)}%
                      </span>
                    </div>
                  </>
                )}
                {quantitativeScore !== null && (
                  <>
                    <span className="text-muted-foreground">|</span>
                    <div
                      className="flex items-center"
                      title={tScore("quantitativeSection")}
                    >
                      <span className="font-medium text-blue-600 dark:text-blue-400">
                        {tScore("quantitativeSectionShort")}:
                      </span>
                      <span className="ms-1 font-medium">
                        {quantitativeScore.toFixed(0)}%
                      </span>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Filter Controls Card */}
      <Card>
        <CardContent className="p-3 sm:p-4">
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center text-sm font-medium text-muted-foreground">
              <FilterIcon className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
              {t("filterBy")}:
            </div>
            <ToggleGroup
              type="single"
              value={filterType}
              variant="outline"
              onValueChange={(value: FilterType) =>
                value && setFilterType(value)
              }
              aria-label={t("filterBy")}
              className="grid w-full grid-cols-3 gap-1 sm:flex sm:w-auto" // Responsive toggle group
            >
              <ToggleGroupItem
                value="all"
                aria-label={t("allQuestionsOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <BookOpen className="h-4 w-4 flex-shrink-0" />{" "}
                {t("allQuestionsOpt")} ({allQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="incorrect"
                aria-label={t("incorrectOnlyOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <ThumbsDown className="h-4 w-4 flex-shrink-0" />{" "}
                {t("incorrectOnlyOpt")} ({incorrectQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="skipped"
                aria-label={t("skippedOnlyOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <HelpCircleIcon className="h-4 w-4 flex-shrink-0" />{" "}
                {t("skippedOnlyOpt")} ({skippedQuestions.length})
              </ToggleGroupItem>
            </ToggleGroup>
          </div>
        </CardContent>
      </Card>

      {/* Subtle loader for filter changes (if data were re-fetched) */}
      {isFetching && !isLoading && (
        <div className="my-4 flex justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary/50" />
        </div>
      )}

      {/* Main Question Review Area */}
      {!isFetching && currentQuestionData ? (
        <div className="space-y-6">
          <ReviewQuestionCard
            questionData={currentQuestionData}
            questionNumber={currentQuestionIndex + 1}
            totalQuestionsInFilter={filteredQuestions.length}
          />
          {filteredQuestions.length > 1 && (
            <div className="mt-6 flex items-center justify-between rounded-lg border bg-card p-2.5 shadow-sm sm:p-3">
              <Button
                onClick={handlePreviousQuestion}
                disabled={currentQuestionIndex === 0}
                variant="ghost"
                size="lg"
                className="text-primary hover:bg-primary/10"
              >
                {locale === "ar" ? (
                  <ChevronRight className="me-1.5 h-5 w-5 rtl:me-0 rtl:ms-1.5" />
                ) : (
                  <ChevronLeft className="me-1.5 h-5 w-5 rtl:me-0 rtl:ms-1.5" />
                )}
                {t("previousQuestion")}
              </Button>
              <span className="text-sm font-medium text-muted-foreground">
                {t("questionXofYShort", {
                  current: currentQuestionIndex + 1,
                  total: filteredQuestions.length,
                })}
              </span>
              <Button
                onClick={handleNextQuestion}
                disabled={currentQuestionIndex >= filteredQuestions.length - 1}
                variant="ghost"
                size="lg"
                className="text-primary hover:bg-primary/10"
              >
                {t("nextQuestion")}
                {locale === "ar" ? (
                  <ChevronLeft className="ms-1.5 h-5 w-5 rtl:me-1.5 rtl:ms-0" />
                ) : (
                  <ChevronRight className="ms-1.5 h-5 w-5 rtl:me-1.5 rtl:ms-0" />
                )}
              </Button>
            </div>
          )}
        </div>
      ) : (
        !isFetching && ( // Only show "No Questions" if not actively fetching
          <Card className="mt-6">
            <CardContent className="flex min-h-[300px] flex-col items-center justify-center p-10 text-center">
              <Frown className="mb-4 h-16 w-16 text-muted-foreground/30" />
              <h3 className="text-xl font-semibold">{t("noQuestionsTitle")}</h3>
              <p className="text-muted-foreground">
                {filterType === "all"
                  ? t("noQuestionsInReview")
                  : t("noQuestionsMatchFilter")}
              </p>
            </CardContent>
          </Card>
        )
      )}
    </div>
  );
};

export default LevelAssessmentReviewPage;
