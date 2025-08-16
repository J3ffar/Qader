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
  ThumbsUp,
  HelpCircle as HelpCircleIcon,
  Loader2,
  AlertTriangle,
  Frown,
  FileText,
  TrendingUp,
  Info,
  ListCollapse,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

import { getTestAttemptReview } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import { UserTestAttemptReviewResponse } from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import ReviewQuestionCard from "@/components/shared/ReviewQuestionCard";
import { queryKeys } from "@/constants/queryKeys";

type FilterType = "all" | "incorrect" | "correct" | "skipped";

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

  const correctQuestions = useMemo(
    () =>
      allQuestions.filter((q) => q.user_answer_details?.is_correct === true),
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
      case "correct":
        return correctQuestions;
      case "skipped":
        return skippedQuestions;
      case "all":
      default:
        return allQuestions;
    }
  }, [filterType, allQuestions, incorrectQuestions, correctQuestions, skippedQuestions]);

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
          onClick={() => router.push(PATHS.STUDY.DETERMINE_LEVEL.LIST)}
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

  // Check if any score data is present at all
  if (
    reviewData.score_percentage === null &&
    reviewData.score_verbal === null &&
    reviewData.score_quantitative === null
  ) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert variant="default" className="max-w-md text-center">
          <Info className="mx-auto mb-2 h-6 w-6" />
          <AlertTitle>{t("errors.scoreDataMissingTitle")}</AlertTitle>
          <AlertDescription>
            {t("errors.scoreDataMissingDescription")}
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
          {t("backToOverview")}
        </Button>
      </div>
    );
  }

  // CORRECTED: Destructure scores directly from the reviewData object
  const { score_percentage, score_verbal, score_quantitative } = reviewData;

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      {/* Header Card */}
      <Card
        dir={locale === "en" ? "ltr" : "rtl"}
        className="overflow-hidden shadow-md dark:bg-[#0B1739] border-2 dark:border-[#7E89AC]"
      >
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            {/* --- MODIFIED HEADER SECTION --- */}
            <div className="flex flex-grow items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => router.push(PATHS.STUDY.DETERMINE_LEVEL.LIST)} // MODIFIED: Go to list page
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
                {t("reviewYourAttempt")}
              </h1>
            </div>

            {/* NEW: View Details Button */}
            <Button asChild variant="default" size="sm">
              <Link href={PATHS.STUDY.DETERMINE_LEVEL.DETAILS(attemptId)}>
                <ListCollapse className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                {t("viewDetails")}
              </Link>
            </Button>
          </div>

          {/* Score display section (moved below for better layout on small screens) */}
          {score_percentage !== null && (
            <div className="mt-3 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 rounded-lg border bg-background p-2 px-3 text-xs shadow-sm sm:text-sm">
              <div className="flex items-center" title={tScore("overallScore")}>
                <TrendingUp className="me-1 h-4 w-4 text-primary" />
                <span className="font-medium">
                  {score_percentage.toFixed(0)}%
                </span>
              </div>
              {score_verbal !== null && (
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
                      {score_verbal.toFixed(0)}%
                    </span>
                  </div>
                </>
              )}
              {score_quantitative !== null && (
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
                      {score_quantitative.toFixed(0)}%
                    </span>
                  </div>
                </>
              )}
            </div>
          )}
        </CardHeader>
      </Card>

      {/* Filter Controls Card */}
      <Card
        dir={locale === "en" ? "ltr" : "rtl"}
        className="dark:bg-[#0B1739] border-2 dark:border-[#7E89AC]"
      >
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
              className="grid w-full grid-cols-2 gap-1 sm:flex sm:w-auto"
            >
              <ToggleGroupItem
                value="all"
                aria-label={t("allQuestionsOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <BookOpen className="h-4 w-4" /> 
                <span className="hidden sm:inline">{t("allQuestionsOpt")}</span>
                <span className="sm:hidden">الكل</span>
                ({allQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="skipped"
                aria-label={t("skippedOnlyOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <HelpCircleIcon className="h-4 w-4" /> 
                <span className="hidden sm:inline">{t("skippedOnlyOpt")}</span>
                <span className="sm:hidden">المتجاوزة</span>
                ({skippedQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="incorrect"
                aria-label={t("incorrectOnlyOptFull")}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <ThumbsDown className="h-4 w-4" /> 
                <span className="hidden sm:inline">{t("incorrectOnlyOpt")}</span>
                <span className="sm:hidden">الخاطئة</span>
                ({incorrectQuestions.length})
              </ToggleGroupItem>
              <ToggleGroupItem
                value="correct"
                aria-label={  "الأسئلة الصحيحة"}
                className="flex-1 justify-center gap-1.5 px-2 sm:px-3"
              >
                <ThumbsUp className="h-4 w-4" /> 
                <span className="hidden sm:inline">{ "الصحيحة"}</span>
                <span className="sm:hidden">الصحيحة</span>
                ({correctQuestions.length})
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
            attemptId={attemptId}
          />
          {filteredQuestions.length > 1 && (
            <div className="mt-6 flex items-center justify-between rounded-lg bg-card p-2.5 shadow-sm sm:p-3 dark:bg-[#0B1739] border-2 dark:border-[#7E89AC]">
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
            <div className="grid w-full grid-cols-2 gap-1 sm:flex sm:w-auto">
              <Skeleton className="h-9 flex-1 rounded-md" />
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

export default LevelAssessmentReviewPage;
