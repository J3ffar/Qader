"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import {
  ArrowLeft,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Filter,
  ListChecks,
  ThumbsDown,
  HelpCircle,
  Loader2,
  AlertTriangle,
  Frown,
  //   Scoreboard,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Skeleton } from "@/components/ui/skeleton";
import ReviewQuestionCard from "@/components/features/platform/study/determine-level/ReviewQuestionCard";

import { getTestAttemptReview } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import type {
  UserTestAttemptReview,
  UserTestAttemptReviewQuestion,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

type FilterType = "all" | "incorrect" | "skipped";
type TestAttemptReviewQueryKey = readonly [
  string,
  string,
  { readonly incorrect_only: boolean | string }
];

const LevelAssessmentReviewPage = () => {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations("Study.determineLevel.review");
  const tCommon = useTranslations("Common");
  const locale = params.locale as string;
  const attemptId = params.attemptId as string;

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [filterType, setFilterType] = useState<FilterType>("all");

  const {
    data: reviewData,
    isLoading,
    error: queryError,
  } = useQuery<
    UserTestAttemptReview, // TQueryFnData: Type returned by queryFn
    Error, // TError
    UserTestAttemptReview, // TData: Type of data property (after select, or TQueryFnData if no select)
    // TQueryKey: This is the crucial part. It should match the structure of your queryKey value.
    // Using a tuple type that accurately describes the key:
    // [string (for QUERY_KEYS...), string (for attemptId), object (for params)]
    readonly [string, string, { readonly incorrect_only: boolean }]
  >({
    queryKey: [
      QUERY_KEYS.USER_TEST_ATTEMPT_REVIEW,
      attemptId,
      { incorrect_only: false },
    ] as const, // Using boolean `false` in the key for caching purposes
    queryFn: () => getTestAttemptReview(attemptId, { incorrect_only: "false" }), // API call expects string "false"
    enabled: !!attemptId,
    staleTime: 10 * 60 * 1000, // Review data doesn't change often
  });

  const allQuestions = useMemo(() => reviewData?.questions || [], [reviewData]);

  const filteredQuestions = useMemo(() => {
    if (!allQuestions.length) return [];
    let questionsToFilter = allQuestions;
    if (filterType === "incorrect") {
      return questionsToFilter.filter(
        (q) => q.user_answer !== null && q.user_is_correct === false
      );
    }
    if (filterType === "skipped") {
      return questionsToFilter.filter((q) => q.user_answer === null);
    }
    return questionsToFilter; // "all"
  }, [allQuestions, filterType]);

  // Reset index when filter changes or data loads
  useEffect(() => {
    setCurrentQuestionIndex(0);
  }, [filterType, filteredQuestions.length]);

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
    // Delegate to loading.tsx via Next.js file conventions
    // This component won't render its own skeleton if loading.tsx exists.
    // However, if it's a direct return from useQuery, we might show a simple loader here.
    // For now, assuming loading.tsx handles the full page skeleton.
    // To be robust, we can add a simple loader if needed.
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }

  if (queryError || !reviewData) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert variant="destructive" className="max-w-lg text-center">
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

  const overallScore = reviewData.score_percentage;
  const verbalScore = reviewData.score_verbal;
  const quantitativeScore = reviewData.score_quantitative;

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      {/* Header Section: Score Summary & Back Button */}
      <div className="mb-6 flex flex-col items-center justify-between gap-4 sm:flex-row">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() =>
              router.push(PATHS.STUDY.DETERMINE_LEVEL.SCORE(attemptId))
            }
            aria-label={t("backToScorePage")}
          >
            {locale === "ar" ? (
              <ArrowRight className="h-5 w-5" />
            ) : (
              <ArrowLeft className="h-5 w-5" />
            )}
          </Button>
          <h1 className="text-2xl font-bold">{t("reviewYourAttempt")}</h1>
        </div>
        {overallScore !== null && overallScore !== undefined && (
          <Card className="p-3 shadow-sm">
            <div className="flex items-center gap-3 text-sm">
              {/* <Scoreboard className="h-5 w-5 text-primary" /> */}
              <span>
                {t("overallScore")}:{" "}
                <strong className="text-primary">
                  {overallScore.toFixed(0)}%
                </strong>
              </span>
              {verbalScore !== null && (
                <span>
                  {t("verbal")}: <strong>{verbalScore.toFixed(0)}%</strong>
                </span>
              )}
              {quantitativeScore !== null && (
                <span>
                  {t("quantitative")}:{" "}
                  <strong>{quantitativeScore.toFixed(0)}%</strong>
                </span>
              )}
            </div>
          </Card>
        )}
      </div>

      {/* Filter Controls */}
      <div className="flex flex-col items-center justify-between gap-4 rounded-lg border bg-card p-4 shadow-sm sm:flex-row">
        <div className="flex items-center text-sm font-medium">
          <Filter className="me-2 h-5 w-5 text-muted-foreground rtl:me-2 rtl:ms-2" />
          {t("filterBy")}:
        </div>
        <ToggleGroup
          type="single"
          value={filterType}
          variant="outline"
          onValueChange={(value: FilterType) => {
            if (value) setFilterType(value);
          }}
          aria-label={t("filterBy")}
          className="max-w-full flex-wrap justify-center sm:justify-end"
        >
          <ToggleGroupItem value="all" aria-label={t("allQuestionsOpt")}>
            <ListChecks className="me-2 h-4 w-full rtl:me-0 rtl:ms-2" />{" "}
            {t("allQuestionsOpt")}
          </ToggleGroupItem>
          <ToggleGroupItem value="incorrect" aria-label={t("incorrectOnlyOpt")}>
            <ThumbsDown className="me-2 h-4 w-full rtl:me-0 rtl:ms-2" />{" "}
            {t("incorrectOnlyOpt")}
          </ToggleGroupItem>
          <ToggleGroupItem value="skipped" aria-label={t("skippedOnlyOpt")}>
            <HelpCircle className="me-2 h-4 w-full rtl:me-0 rtl:ms-2" />{" "}
            {t("skippedOnlyOpt")}
          </ToggleGroupItem>
        </ToggleGroup>
      </div>

      {/* Main Question Review Area */}
      {filteredQuestions.length > 0 && currentQuestionData ? (
        <div className="space-y-6">
          <ReviewQuestionCard
            questionData={currentQuestionData}
            questionNumber={currentQuestionIndex + 1}
            totalQuestionsInFilter={filteredQuestions.length}
          />

          {/* Navigation Controls */}
          <div className="mt-6 flex items-center justify-between">
            <Button
              onClick={handlePreviousQuestion}
              disabled={currentQuestionIndex === 0}
              variant="outline"
              size="lg"
            >
              {locale === "ar" ? (
                <ChevronRight className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
              ) : (
                <ChevronLeft className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
              )}
              {t("previousQuestion")}
            </Button>
            <span className="text-sm text-muted-foreground">
              {t("questionXofY", {
                current: currentQuestionIndex + 1,
                total: filteredQuestions.length,
              })}
            </span>
            <Button
              onClick={handleNextQuestion}
              disabled={currentQuestionIndex === filteredQuestions.length - 1}
              variant="outline"
              size="lg"
            >
              {t("nextQuestion")}
              {locale === "ar" ? (
                <ChevronLeft className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
              ) : (
                <ChevronRight className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
              )}
            </Button>
          </div>
        </div>
      ) : (
        <Alert className="mx-auto max-w-md">
          <Frown className="h-5 w-5" />
          <AlertTitle>{t("noQuestionsTitle")}</AlertTitle>
          <AlertDescription>
            {filterType === "all"
              ? t("noQuestionsInReview")
              : t("noQuestionsMatchFilter")}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default LevelAssessmentReviewPage;
