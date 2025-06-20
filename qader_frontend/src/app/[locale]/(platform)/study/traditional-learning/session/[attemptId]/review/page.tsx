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
  AlertTriangle,
  Frown,
  FileText,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Skeleton } from "@/components/ui/skeleton";
import ReviewQuestionCard from "@/components/shared/ReviewQuestionCard";

import { getTestAttemptReview } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import { UserTestAttemptReviewResponse } from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";

type FilterType = "all" | "incorrect" | "skipped";

const TraditionalLearningReviewPage = () => {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations("Study.traditionalLearning.review");
  const tCommon = useTranslations("Common");
  const locale = params.locale as string;
  const attemptId = params.attemptId as string;

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [filterType, setFilterType] = useState<FilterType>("all");

  const {
    data: reviewData,
    isLoading,
    error: queryError,
  } = useQuery<UserTestAttemptReviewResponse, Error>({
    queryKey: queryKeys.tests.review(attemptId),
    queryFn: () => getTestAttemptReview(attemptId),
    enabled: !!attemptId,
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const allQuestions = useMemo(() => reviewData?.questions || [], [reviewData]);
  const incorrectQuestions = useMemo(
    () =>
      allQuestions.filter((q) => q.user_answer_details?.is_correct === false),
    [allQuestions]
  );
  const skippedQuestions = useMemo(
    () =>
      allQuestions.filter(
        (q) => q.user_answer_details?.selected_choice === null
      ),
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

  useEffect(() => {
    setCurrentQuestionIndex(0);
  }, [filterType, allQuestions.length]);

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

  if (isLoading) return <ReviewPageSkeleton />;

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
          onClick={() => router.push(PATHS.STUDY.TRADITIONAL_LEARNING.LIST)}
          variant="outline"
          className="mt-6"
        >
          {locale === "ar" ? (
            <ArrowRight className="me-2 h-4 w-4" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4" />
          )}
          {t("backToList")}
        </Button>
      </div>
    );
  }

  const { score_percentage } = reviewData;

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      {/* Header Card */}
      <Card className="overflow-hidden shadow-md">
        <CardHeader>
          <div className="flex flex-col-reverse items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h1 className="flex items-center text-xl font-semibold text-primary sm:text-2xl">
              <FileText className="me-2.5 h-[1.3em] w-[1.3em]" />
              {t("pageTitle")}
            </h1>
            <Button
              asChild
              variant="outline"
              size="sm"
              className="w-full sm:w-auto"
            >
              <Link href={PATHS.STUDY.TRADITIONAL_LEARNING.SCORE(attemptId)}>
                {locale === "ar" ? (
                  <ArrowRight className="me-2 h-4 w-4" />
                ) : (
                  <ArrowLeft className="me-2 h-4 w-4" />
                )}
                {t("backToScore")}
              </Link>
            </Button>
          </div>

          {score_percentage !== null && (
            <div className="mt-4 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 rounded-lg border bg-background p-2 px-3 text-sm shadow-sm">
              <div className="flex items-center font-medium">
                <TrendingUp className="me-1.5 h-4 w-4 text-primary" />
                <span>{tCommon("overallScore")}:</span>
                <span className="ms-1.5">{score_percentage.toFixed(0)}%</span>
              </div>
            </div>
          )}
        </CardHeader>
      </Card>

      {/* Filter Controls Card */}
      <Card>
        <CardContent>
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center text-sm font-medium text-muted-foreground">
              <FilterIcon className="me-2 h-4 w-4" />
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
              className="grid w-full grid-cols-3 gap-1 sm:flex sm:w-auto"
            >
              <ToggleGroupItem
                value="all"
                aria-label={t("allQuestionsOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <BookOpen className="h-4 w-4" /> {t("allQuestionsOpt")} (
                {allQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="incorrect"
                aria-label={t("incorrectOnlyOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <ThumbsDown className="h-4 w-4" /> {t("incorrectOnlyOpt")} (
                {incorrectQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="skipped"
                aria-label={t("skippedOnlyOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <HelpCircleIcon className="h-4 w-4" /> {t("skippedOnlyOpt")} (
                {skippedQuestions.length})
              </ToggleGroupItem>
            </ToggleGroup>
          </div>
        </CardContent>
      </Card>

      {/* Main Question Review Area */}
      {currentQuestionData ? (
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
                  <ChevronRight className="me-1.5 h-5 w-5" />
                ) : (
                  <ChevronLeft className="me-1.5 h-5 w-5" />
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
                  <ChevronLeft className="ms-1.5 h-5 w-5" />
                ) : (
                  <ChevronRight className="ms-1.5 h-5 w-5" />
                )}
              </Button>
            </div>
          )}
        </div>
      ) : (
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
      )}
    </div>
  );
};

const ReviewPageSkeleton = () => {
  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      {/* Header Card Skeleton */}
      <Card>
        <CardHeader>
          <div className="flex flex-col-reverse items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
            <Skeleton className="h-8 w-56" /> {/* Title */}
            <Skeleton className="h-9 w-32" /> {/* Back Button */}
          </div>
          <div className="mt-4 flex items-center justify-center">
            <Skeleton className="h-8 w-48" /> {/* Score */}
          </div>
        </CardHeader>
      </Card>

      {/* Filter Controls Card Skeleton */}
      <Card>
        <CardContent className="p-3 sm:p-4">
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center text-sm">
              <FilterIcon className="me-2 h-4 w-4 text-muted-foreground/50 rtl:me-0 rtl:ms-2" />
              <Skeleton className="h-5 w-16" />
            </div>
            <div className="grid w-full grid-cols-3 gap-1 sm:flex sm:w-auto">
              <Skeleton className="h-9 flex-1 rounded-md" />
              <Skeleton className="h-9 flex-1 rounded-md" />
              <Skeleton className="h-9 flex-1 rounded-md" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Question Card Skeleton */}
      <Card className="w-full shadow-lg">
        <CardHeader>
          <div className="mb-3 flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
            <Skeleton className="h-5 w-28" />
            <Skeleton className="h-7 w-24 rounded-md" />
          </div>
          <Skeleton className="mb-2 h-6 w-full" />
          <Skeleton className="h-6 w-4/5" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-px w-full bg-border" />
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="flex items-start space-x-3 rounded-md border p-3.5 rtl:space-x-reverse"
              >
                <Skeleton className="mt-0.5 h-5 w-5 flex-shrink-0 rounded-full" />
                <Skeleton className="mt-0.5 h-5 w-6" />
                <Skeleton className="h-5 flex-1" />
              </div>
            ))}
          </div>
          <Skeleton className="mt-4 h-12 w-full rounded-md" />{" "}
          <Skeleton className="mt-2 h-12 w-full rounded-md" />
        </CardContent>
      </Card>

      {/* Navigation Controls Skeleton */}
      <div className="mt-6 flex items-center justify-between rounded-lg border bg-card p-2.5 shadow-sm sm:p-3">
        <Skeleton className="h-11 w-32 rounded-md sm:w-36" />
        <Skeleton className="h-5 w-20 sm:w-24" />
        <Skeleton className="h-11 w-32 rounded-md sm:w-36" />
      </div>
    </div>
  );
};

export default TraditionalLearningReviewPage;
