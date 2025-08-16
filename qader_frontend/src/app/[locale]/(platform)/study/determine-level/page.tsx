"use client";

import React, { useState, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { PencilLine, ListFilter } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

import { getTestAttempts, cancelTestAttempt } from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import {
  PaginatedUserTestAttempts,
  UserTestAttemptList,
} from "@/types/api/study.types";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { AttemptActionButtons } from "./_components/AttemptActionButtons";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { queryKeys } from "@/constants/queryKeys";
import { useParams } from "next/navigation";

// Constants
const PAGE_SIZE = 20;

// =================================================================
// HELPER FUNCTIONS
// =================================================================

const getBadgeStyle = (levelKey?: string): string => {
  if (!levelKey)
    return "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200";
  switch (levelKey) {
    case "excellent":
      return "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100";
    case "veryGood":
      return "bg-blue-100 text-blue-700 dark:bg-blue-700 dark:text-blue-100";
    case "good":
      return "bg-yellow-100 text-yellow-700 dark:bg-yellow-700 dark:text-yellow-100";
    case "weak":
      return "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100";
    case "notApplicable":
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200";
  }
};

const mapScoreToLevelKey = (score: number | null | undefined): string => {
  if (score === null || score === undefined) {
    return "notApplicable";
  }
  if (score >= 90) return "excellent";
  if (score >= 80) return "veryGood";
  if (score >= 65) return "good";
  return "weak";
};

// =================================================================
// COMPONENT IMPLEMENTATION
// =================================================================

const LevelAssessmentPage = () => {
  const t = useTranslations("Study.determineLevel");
  const tBadge = useTranslations("Study.determineLevel.badgeColors");
  const tActions = useTranslations("Study.determineLevel.actions");
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<"date" | "percentage">("date");

  const ordering = sortBy === "date" ? "-date" : "-score_percentage";

  const {
    data: attemptsData,
    isLoading,
    isFetching,
    error,
  } = useQuery<PaginatedUserTestAttempts, Error>({
    queryKey: queryKeys.tests.list({
      attempt_type: "level_assessment",
      page,
      ordering,
    }),
    queryFn: () =>
      getTestAttempts({
        attempt_type: "level_assessment",
        page,
        ordering,
      }),
  });

  const cancelAttemptMutation = useMutation({
    mutationFn: cancelTestAttempt,
    onSuccess: (_, attemptId) => {
      toast.success(tActions("cancelDialog.successToast", { attemptId }));
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
    },
    onError: (err: any) => {
      const errorMessage = getApiErrorMessage(
        err,
        tActions("cancelDialog.errorToastGeneric")
      );
      toast.error(errorMessage);
    },
  });

  const { attempts, pageCount, canPreviousPage, canNextPage } = useMemo(() => {
    const results = attemptsData?.results ?? [];

    const enhancedAttempts = results.map((attempt) => ({
      ...attempt,
      quantitative_level_key: mapScoreToLevelKey(
        attempt.performance?.quantitative
      ),
      verbal_level_key: mapScoreToLevelKey(attempt.performance?.verbal),
    }));

    return {
      attempts: enhancedAttempts,
      pageCount: attemptsData?.count
        ? Math.ceil(attemptsData.count / PAGE_SIZE)
        : 1,
      canPreviousPage: !!attemptsData?.previous,
      canNextPage: !!attemptsData?.next,
    };
  }, [attemptsData]);

  const handleSortChange = (value: "date" | "percentage") => {
    setPage(1);
    setSortBy(value);
  };

  if (isLoading) {
    return <DetermineLevelPageSkeleton />;
  }

  if (error) {
    return (
      <div className="container mx-auto p-3 sm:p-4 md:p-6 lg:p-8 max-w-7xl">
        <Alert variant="destructive" className="mx-auto max-w-2xl">
          <AlertTitle className="text-base sm:text-lg">{t("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription className="text-sm sm:text-base">
            {getApiErrorMessage(error, t("errors.fetchFailedDescription"))}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const hasNoAttemptsAtAll = !attemptsData?.count;

  if (hasNoAttemptsAtAll) {
    return (
      <div className="flex min-h-[calc(100vh-100px)] sm:min-h-[calc(100vh-150px)] flex-col items-center justify-center p-4 text-center">
        <Image
          src="/images/search.png"
          width={120}
          height={120}
          alt={t("noAttemptsTitle")}
          className="mb-4 sm:mb-6 w-20 h-20 sm:w-[120px] sm:h-[120px]"
        />
        <h2 className="mb-2 text-xl sm:text-2xl font-[700] dark:text-white">
          {t("noAttemptsTitle")}
        </h2>
        <p className="mb-4 sm:mb-6 max-w-xs sm:max-w-md text-sm sm:text-base text-muted-foreground dark:text-gray-300">
          {t("noAttemptsDescription")}
        </p>
        <Button asChild size="lg" className="w-full sm:w-auto md:w-[250px]">
          <Link href={PATHS.STUDY.DETERMINE_LEVEL.START}>
            <PencilLine className="me-2 h-4 w-4 sm:h-5 sm:w-5 rtl:me-0 rtl:ms-2" />
            {t("startTest")}
          </Link>
        </Button>
      </div>
    );
  }

  const {locale} = useParams();

  return (
    <div className="container mx-auto space-y-4 sm:space-y-6 p-3 sm:p-4 md:p-6 lg:p-8 max-w-7xl">
      <Card className="dark:bg-[#0B1739] dark:border-[#7E89AC] border-2">
        <CardHeader 
          dir={locale === "en" ? "ltr" : "rtl"} 
          className="flex flex-col justify-between gap-3 sm:gap-4 p-4 sm:p-6 md:flex-row md:items-center"
        >
          <div className="space-y-1">
            <CardTitle className="text-xl sm:text-2xl font-bold">
              {t("title")}
            </CardTitle>
            <p className="text-xs sm:text-sm text-muted-foreground">
              {t("description")}
            </p>
          </div>
          <Button asChild className="text-white w-full sm:w-auto" size="default">
            <Link href={PATHS.STUDY.DETERMINE_LEVEL.START}>
              <PencilLine className="me-2 h-4 w-4 sm:h-5 sm:w-5 rtl:me-0 rtl:ms-2" />
              {t("retakeTest")}
            </Link>
          </Button>
        </CardHeader>
        
        <CardContent dir={locale === "en" ? "ltr" : "rtl"} className="p-3 sm:p-4 md:p-6">
          {/* Sort Controls */}
          <div className="mb-4 sm:mb-6 flex flex-col justify-between gap-3 sm:gap-4 rounded-lg border bg-card p-3 sm:p-4 sm:flex-row sm:items-center dark:bg-[#0B1739]">
            <h3 className="text-base sm:text-lg font-semibold">
              {t("attemptsLogTitle")}
            </h3>
            <div className="flex items-center gap-2">
              <ListFilter className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
              <Select
                value={sortBy}
                onValueChange={handleSortChange}
                dir={
                  typeof document !== "undefined"
                    ? (document.documentElement.dir as "rtl" | "ltr")
                    : "ltr"
                }
              >
                <SelectTrigger className="w-full sm:w-[180px]">
                  <SelectValue placeholder={t("sortBy")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">{t("latestDate")}</SelectItem>
                  <SelectItem value="percentage">
                    {t("highestPercentage")}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Desktop/Tablet Table - Show from md breakpoint */}
          <div className="hidden rounded-xl border overflow-x-auto md:block">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className={cn(locale === "en" ? "text-left" : "text-right", "whitespace-nowrap")}>
                    {t("attemptsTable.date")}
                  </TableHead>
                  <TableHead className="text-center whitespace-nowrap">
                    {t("attemptsTable.numQuestions")}
                  </TableHead>
                  <TableHead className="text-center whitespace-nowrap">
                    {t("attemptsTable.percentage")}
                  </TableHead>
                  <TableHead className="text-center whitespace-nowrap min-w-[120px]">
                    {t("attemptsTable.quantitativePerformance")}
                  </TableHead>
                  <TableHead className="text-center whitespace-nowrap min-w-[120px]">
                    {t("attemptsTable.verbalPerformance")}
                  </TableHead>
                  <TableHead className="text-center whitespace-nowrap">
                    {t("attemptsTable.status")}
                  </TableHead>
                  <TableHead className="w-[200px] lg:w-[280px] text-center whitespace-nowrap">
                    {t("attemptsTable.actions")}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {attempts.map((attempt) => (
                  <TableRow
                    key={attempt.attempt_id}
                    className={cn({
                      "opacity-60": attempt.status === "abandoned",
                    })}
                  >
                    <TableCell className="whitespace-nowrap">
                      {new Date(attempt.date).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </TableCell>
                    <TableCell className="text-center">
                      {attempt.num_questions}
                    </TableCell>
                    <TableCell className="text-center font-medium">
                      {attempt.score_percentage !== null
                        ? `${attempt.score_percentage.toFixed(0)}%`
                        : attempt.status === "started"
                        ? t("attemptsTable.statusInProgress")
                        : "-"}
                    </TableCell>
                    <TableCell className="text-center">
                      <span
                        className={cn(
                          "inline-block rounded-md px-1.5 py-0.5 sm:px-2 sm:py-1 text-xs font-medium",
                          getBadgeStyle(attempt.quantitative_level_key)
                        )}
                      >
                        {tBadge(attempt.quantitative_level_key)}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span
                        className={cn(
                          "inline-block rounded-md px-1.5 py-0.5 sm:px-2 sm:py-1 text-xs font-medium",
                          getBadgeStyle(attempt.verbal_level_key)
                        )}
                      >
                        {tBadge(attempt.verbal_level_key)}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span
                        className={cn(
                          "inline-block rounded-md px-1.5 py-0.5 sm:px-2 sm:py-1 text-xs font-medium",
                          {
                            "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100":
                              attempt.status === "completed",
                            "bg-yellow-100 text-yellow-700 dark:bg-yellow-700 dark:text-yellow-100":
                              attempt.status === "started",
                            "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100":
                              attempt.status === "abandoned",
                          }
                        )}
                      >
                        {attempt.status_display || attempt.status}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <AttemptActionButtons
                        attempt={attempt}
                        cancelAttemptMutation={cancelAttemptMutation}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile Accordion - Show only on mobile */}
          <div className="space-y-2 sm:space-y-3 md:hidden">
            <Accordion type="single" collapsible className="w-full space-y-2">
              {attempts.map((attempt) => (
                <AccordionItem
                  value={`item-${attempt.attempt_id}`}
                  key={attempt.attempt_id}
                  className="rounded-lg border dark:border-gray-700 overflow-hidden"
                  disabled={attempt.status === "abandoned"}
                >
                  <AccordionTrigger className="p-3 sm:p-4 hover:no-underline disabled:opacity-60">
                    <div className="flex w-full items-center justify-between gap-2">
                      <div className="text-start rtl:text-right space-y-1">
                        <p className="text-sm sm:text-base font-medium">
                          {new Date(attempt.date).toLocaleDateString(
                            undefined,
                            { year: "numeric", month: "short", day: "numeric" }
                          )}
                        </p>
                        <p className="text-xs sm:text-sm text-muted-foreground">
                          {t("attemptsTable.percentage")}:{" "}
                          <span className="font-medium">
                            {attempt.score_percentage !== null
                              ? `${attempt.score_percentage.toFixed(0)}%`
                              : attempt.status === "started"
                              ? t("attemptsTable.statusInProgress")
                              : "-"}
                          </span>
                        </p>
                      </div>
                      <span
                        className={cn(
                          "flex-shrink-0 rounded-md px-1.5 py-0.5 sm:px-2 sm:py-1 text-xs font-medium",
                          {
                            "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100":
                              attempt.status === "completed",
                            "bg-yellow-100 text-yellow-700 dark:bg-yellow-700 dark:text-yellow-100":
                              attempt.status === "started",
                            "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100":
                              attempt.status === "abandoned",
                          }
                        )}
                      >
                        {attempt.status_display || attempt.status}
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="p-3 sm:p-4 pt-0">
                    <div className="space-y-2 text-xs sm:text-sm">
                      <div className="flex justify-between items-center">
                        <strong>{t("attemptsTable.numQuestions")}:</strong>
                        <span>{attempt.num_questions}</span>
                      </div>
                      <div className="flex justify-between items-center gap-2">
                        <strong className="flex-shrink-0">
                          {t("attemptsTable.quantitativePerformance")}:
                        </strong>
                        <span
                          className={cn(
                            "rounded-md px-1.5 py-0.5 text-xs",
                            getBadgeStyle(attempt.quantitative_level_key)
                          )}
                        >
                          {tBadge(attempt.quantitative_level_key)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center gap-2">
                        <strong className="flex-shrink-0">
                          {t("attemptsTable.verbalPerformance")}:
                        </strong>
                        <span
                          className={cn(
                            "rounded-md px-1.5 py-0.5 text-xs",
                            getBadgeStyle(attempt.verbal_level_key)
                          )}
                        >
                          {tBadge(attempt.verbal_level_key)}
                        </span>
                      </div>
                      <div className="mt-3 pt-3 border-t">
                        <AttemptActionButtons
                          attempt={attempt}
                          cancelAttemptMutation={cancelAttemptMutation}
                        />
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>

          {/* Pagination */}
          <DataTablePagination
            page={page}
            pageCount={pageCount}
            setPage={setPage}
            canPreviousPage={canPreviousPage}
            canNextPage={canNextPage}
            isFetching={isFetching}
            className="mt-4"
          />
        </CardContent>
      </Card>
    </div>
  );
};

// Responsive Skeleton component
const DetermineLevelPageSkeleton = () => {
  return (
    <div className="container mx-auto space-y-4 sm:space-y-6 p-3 sm:p-4 md:p-6 lg:p-8 max-w-7xl">
      <Card>
        <CardHeader className="flex flex-col justify-between gap-3 sm:gap-4 p-4 sm:p-6 md:flex-row md:items-center">
          <div>
            <Skeleton className="mb-2 h-6 sm:h-8 w-32 sm:w-48" />
            <Skeleton className="h-3 sm:h-4 w-48 sm:w-72" />
          </div>
          <Skeleton className="h-9 sm:h-10 w-full sm:w-48" />
        </CardHeader>
        <CardContent className="p-3 sm:p-4 md:p-6">
          <div className="mb-4 sm:mb-6 flex flex-col justify-between gap-3 sm:gap-4 rounded-lg border bg-background p-3 sm:p-4 sm:flex-row sm:items-center">
            <Skeleton className="h-5 sm:h-7 w-32 sm:w-40" />
            <Skeleton className="h-9 sm:h-10 w-full sm:w-[180px]" />
          </div>

          {/* Desktop skeleton */}
          <div className="hidden rounded-xl border md:block overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  {[...Array(7)].map((_, i) => (
                    <TableHead key={i}>
                      <Skeleton className="h-4 sm:h-5 w-20 sm:w-24" />
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {[...Array(3)].map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Skeleton className="h-4 sm:h-5 w-16 sm:w-20" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="mx-auto h-4 sm:h-5 w-8 sm:w-10" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="mx-auto h-4 sm:h-5 w-8 sm:w-10" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-5 sm:h-6 w-14 sm:w-16" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-5 sm:h-6 w-14 sm:w-16" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="mx-auto h-5 sm:h-6 w-16 sm:w-20" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="mx-auto h-8 sm:h-9 w-28 sm:w-32" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile skeleton */}
          <div className="space-y-2 sm:space-y-3 md:hidden">
            {[...Array(3)].map((_, i) => (
              <div
                key={`skeleton-mobile-${i}`}
                className="flex items-center justify-between rounded-lg border p-3 sm:p-4 dark:border-gray-700"
              >
                <div className="text-start rtl:text-right space-y-1">
                  <Skeleton className="h-4 sm:h-5 w-20 sm:w-24" />
                  <Skeleton className="h-3 sm:h-4 w-28 sm:w-32" />
                </div>
                <Skeleton className="h-5 sm:h-6 w-16 sm:w-20" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LevelAssessmentPage;
