"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
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
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

import { getTestAttemptReview } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import { UserTestAttemptReviewResponse } from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import ReviewQuestionCard from "@/components/shared/ReviewQuestionCard";

type FilterType = "all" | "incorrect" | "skipped";

const TestReviewPage = () => {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const t = useTranslations("Study.tests.review");
  const tCommon = useTranslations("Common");
  const locale = params.locale as string;
  const attemptId = params.attemptId as string;

  const initialFilter =
    searchParams.get("incorrect_only") === "true" ? "incorrect" : "all";
  const [filterType, setFilterType] = useState<FilterType>(initialFilter);

  const {
    data: reviewData,
    isLoading,
    error: queryError,
  } = useQuery<UserTestAttemptReviewResponse, Error>({
    queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_REVIEW, attemptId],
    queryFn: () => getTestAttemptReview(attemptId),
    staleTime: 10 * 60 * 1000,
  });

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const {
    allQuestions,
    incorrectQuestions,
    skippedQuestions,
    filteredQuestions,
  } = useMemo(() => {
    const all = reviewData?.questions || [];
    const incorrect = all.filter(
      (q) => q.user_answer_details?.is_correct === false
    );
    const skipped = all.filter(
      (q) => q.user_answer_details?.selected_choice === null
    );

    let filtered;
    switch (filterType) {
      case "incorrect":
        filtered = incorrect;
        break;
      case "skipped":
        filtered = skipped;
        break;
      default:
        filtered = all;
    }
    return {
      allQuestions: all,
      incorrectQuestions: incorrect,
      skippedQuestions: skipped,
      filteredQuestions: filtered,
    };
  }, [reviewData, filterType]);

  useEffect(() => {
    setCurrentQuestionIndex(0);
  }, [filterType]);

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
    // ... Error handling UI (same as example, but with updated paths)
    return (
      <div className="container mx-auto p-6 text-center">
        <Alert variant="destructive">
          <AlertTitle>{tCommon("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(queryError, t("errors.fetchReviewFailed"))}
          </AlertDescription>
        </Alert>
        <Button
          onClick={() => router.push(PATHS.STUDY.TESTS.LIST)}
          variant="outline"
          className="mt-6"
        >
          {t("backToList")}
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      <Card>
        <CardHeader>
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-grow items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => router.push(PATHS.STUDY.TESTS.LIST)} // MODIFIED: Go to list page
                aria-label={t("backToList")} // MODIFIED: Aria label
                className="text-primary hover:bg-primary/10"
              >
                {locale === "ar" ? (
                  <ArrowRight className="h-5 w-5" />
                ) : (
                  <ArrowLeft className="h-5 w-5" />
                )}
              </Button>
              <h1 className="flex items-center text-xl font-semibold text-primary sm:text-2xl">
                <FileText className="me-2.5 h-[1.3em] w-[1.3em]" />
                {t("pageTitle")}
              </h1>
            </div>
            <Button asChild variant="default" size="sm">
              <Link href={PATHS.STUDY.TESTS.SCORE(attemptId)}>
                <Sparkles className="me-2 h-4 w-4" />
                {t("backToScore")}
              </Link>
            </Button>
          </div>
        </CardHeader>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center text-sm font-medium text-muted-foreground">
              <FilterIcon className="me-2 h-4 w-4" />
              {t("filterBy")}
            </div>
            <ToggleGroup
              type="single"
              value={filterType}
              onValueChange={(value: FilterType) =>
                value && setFilterType(value)
              }
              className="grid w-full flex-1 grid-cols-3 gap-1 sm:flex sm:w-auto"
            >
              <ToggleGroupItem
                value="all"
                aria-label={t("allQuestionsOptFull")}
                className="flex-1 justify-center gap-1.5"
              >
                <BookOpen className="h-4 w-4" />
                {t("allQuestionsOpt")} ({allQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="incorrect"
                aria-label={t("incorrectOnlyOptFull")}
                className="flex-1 justify-center gap-1.5"
              >
                <ThumbsDown className="h-4 w-4" />
                {t("incorrectOnlyOpt")} ({incorrectQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="skipped"
                aria-label={t("skippedOnlyOptFull")}
                className="flex-1 justify-center gap-1.5"
              >
                <HelpCircleIcon className="h-4 w-4" />
                {t("skippedOnlyOpt")} ({skippedQuestions.length})
              </ToggleGroupItem>
            </ToggleGroup>
          </div>
        </CardContent>
      </Card>

      {currentQuestionData ? (
        <div className="space-y-6">
          <ReviewQuestionCard
            questionData={currentQuestionData}
            questionNumber={currentQuestionIndex + 1}
            totalQuestionsInFilter={filteredQuestions.length}
          />
          {filteredQuestions.length > 1 && (
            <div className="mt-6 flex items-center justify-between rounded-lg border bg-card p-2.5 shadow-sm">
              <Button
                onClick={handlePreviousQuestion}
                disabled={currentQuestionIndex === 0}
                variant="ghost"
                size="lg"
              >
                {locale === "ar" ? (
                  <ChevronRight className="me-1.5 h-5 w-5" />
                ) : (
                  <ChevronLeft className="me-1.5 h-5 w-5" />
                )}
                {t("previousQuestion")}
              </Button>
              <Button
                onClick={handleNextQuestion}
                disabled={currentQuestionIndex >= filteredQuestions.length - 1}
                variant="ghost"
                size="lg"
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
      <Card className="overflow-hidden">
        <CardHeader className="bg-muted/20 p-4 sm:p-5">
          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <div className="flex items-center gap-2">
              <Skeleton className="h-10 w-10 rounded-md" /> {/* Back button */}
              <div className="flex items-center gap-2.5">
                <FileText className="h-[1.3em] w-[1.3em] text-muted-foreground/50" />
                <Skeleton className="h-7 w-40 sm:w-56" /> {/* Title */}
              </div>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 rounded-lg border bg-background p-2 px-3">
              <TrendingUp className="me-1 h-4 w-4 text-muted-foreground/50 rtl:me-0 rtl:ms-1" />
              <Skeleton className="h-4 w-10" />
              <Skeleton className="h-4 w-px bg-muted-foreground/20" />
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-px bg-muted-foreground/20" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Filter Controls Card Skeleton */}
      <Card>
        <CardContent className="p-3 sm:p-4">
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center text-sm">
              <FilterIcon className="me-2 h-4 w-4 text-muted-foreground/50 rtl:me-0 rtl:ms-2" />
              <Skeleton className="h-5 w-16" /> {/* "Filter By:" */}
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
            <Skeleton className="h-5 w-28" /> {/* Question X of Y */}
            <Skeleton className="h-7 w-24 rounded-md" /> {/* Status Badge */}
          </div>
          <Skeleton className="mb-2 h-6 w-full" /> {/* Question Text Line 1 */}
          <Skeleton className="h-6 w-4/5" /> {/* Question Text Line 2 */}
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-px w-full bg-border" /> {/* Separator */}
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
          {/* Accordion 1 */}
          <Skeleton className="mt-2 h-12 w-full rounded-md" />{" "}
          {/* Accordion 2 */}
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

export default TestReviewPage;
