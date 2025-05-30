"use client";

import React, { useState, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { PencilLine, ListFilter, FileText, Loader2, Ban } from "lucide-react";

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
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import { UserTestAttemptBrief } from "@/types/api/study.types";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

// Helper to map API level terms (if they exist) or scores to colors/text
// For now, using the existing logic and assuming performance object might contain keys like 'verbal_level_display'
const getBadgeStyle = (level?: string): string => {
  if (!level)
    return "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200";
  switch (level.toLowerCase()) {
    case "ممتاز":
    case "excellent":
      return "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100";
    case "جيد جداً":
    case "very good":
      return "bg-blue-100 text-blue-700 dark:bg-blue-700 dark:text-blue-100";
    case "جيد":
    case "good":
      return "bg-yellow-100 text-yellow-700 dark:bg-yellow-700 dark:text-yellow-100";
    case "ضعيف":
    case "weak":
      return "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100";
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200";
  }
};

const LevelAssessmentPage = () => {
  const t = useTranslations("Study.determineLevel");
  const tBadge = useTranslations("Study.determineLevel.badgeColors");
  const queryClient = useQueryClient();

  const [sortBy, setSortBy] = useState<"date" | "percentage">("date");

  const {
    data: attemptsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: [
      QUERY_KEYS.USER_TEST_ATTEMPTS,
      { attempt_type: "level_assessment" },
    ],
    queryFn: () => getTestAttempts({ attempt_type: "level_assessment" }),
  });

  const cancelAttemptMutation = useMutation({
    mutationFn: cancelTestAttempt,
    onSuccess: (_, attemptId) => {
      toast.success(t("cancelDialog.successToast", { attemptId }));
      queryClient.invalidateQueries({
        queryKey: [
          QUERY_KEYS.USER_TEST_ATTEMPTS,
          { attempt_type: "level_assessment" },
        ],
      });
    },
    onError: (err: any, attemptId) => {
      const errorMessage = getApiErrorMessage(
        err,
        t("cancelDialog.errorToastGeneric")
      );
      toast.error(errorMessage);
    },
  });

  const attempts = useMemo(() => {
    if (!attemptsData?.results) return [];
    const sorted = [...attemptsData.results].sort((a, b) => {
      if (sortBy === "date") {
        return new Date(b.date).getTime() - new Date(a.date).getTime();
      }
      if (sortBy === "percentage") {
        return (b.score_percentage || 0) - (a.score_percentage || 0);
      }
      return 0;
    });
    // The API might return verbal/quantitative performance as numeric.
    // If we need to display qualitative levels ("ممتاز", "ضعيف"),
    // we'd need a mapping function here or expect the API to provide display strings.
    // For now, let's assume `performance` object might have `verbal_level_display` etc.
    return sorted.map((attempt) => ({
      ...attempt,
      verbal_level_display:
        (attempt.performance?.verbal_level_display as string) ||
        tBadge("default"),
      quantitative_level_display:
        (attempt.performance?.quantitative_level_display as string) ||
        tBadge("default"),
    }));
  }, [attemptsData, sortBy, tBadge]);

  const renderActionButtons = (attempt: UserTestAttemptBrief) => {
    const isCancelable = attempt.status === "started"; // Or other cancelable statuses from backend

    return (
      <div className="flex flex-col justify-center gap-2 sm:flex-row">
        <Button variant="outline" size="sm" asChild>
          <Link href={PATHS.STUDY.DETERMINE_LEVEL.REVIEW(attempt.attempt_id)}>
            <FileText className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
            {attempt.status === "completed"
              ? t("attemptsTable.reviewTest")
              : t("attemptsTable.viewDetails")}
          </Link>
        </Button>
        {isCancelable && (
          <ConfirmationDialog
            triggerButton={
              <Button
                variant="destructive"
                size="sm"
                disabled={
                  cancelAttemptMutation.isPending &&
                  cancelAttemptMutation.variables === attempt.attempt_id
                }
              >
                {cancelAttemptMutation.isPending &&
                cancelAttemptMutation.variables === attempt.attempt_id ? (
                  <Loader2 className="me-2 h-4 w-4 animate-spin rtl:me-0 rtl:ms-2" />
                ) : (
                  <Ban className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                )}
                {t("attemptsTable.cancelTest")}
              </Button>
            }
            title={t("cancelDialog.title")}
            description={t("cancelDialog.description", {
              attemptId: attempt.attempt_id,
            })}
            confirmActionText={t("cancelDialog.confirmButton")}
            onConfirm={() => cancelAttemptMutation.mutate(attempt.attempt_id)}
            isConfirming={
              cancelAttemptMutation.isPending &&
              cancelAttemptMutation.variables === attempt.attempt_id
            }
            confirmButtonVariant="destructive"
          />
        )}
      </div>
    );
  };

  if (isLoading) {
    return <DetermineLevelPageSkeleton />;
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 md:p-6 lg:p-8">
        <Alert variant="destructive">
          <AlertTitle>{t("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {t("errors.fetchFailedDescription")}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Show prompt if no attempts or if specifically required (e.g., only 1 attempt logic from old code)
  if (!attempts || attempts.length === 0) {
    // Simplified: show if no attempts
    return (
      <div className="flex min-h-[calc(100vh-150px)] flex-col items-center justify-center p-4 text-center">
        <Image
          src="/images/search.png" // Ensure this image exists in public/images
          width={120}
          height={120}
          alt={t("noAttemptsTitle")}
          className="mb-6"
        />
        <h2 className="mb-2 text-2xl font-semibold dark:text-white">
          {t("noAttemptsTitle")}
        </h2>
        <p className="mb-6 max-w-md text-muted-foreground dark:text-gray-300">
          {t("noAttemptsDescription")}
        </p>
        <Button asChild size="lg">
          <Link href={PATHS.STUDY.DETERMINE_LEVEL.START}>
            <PencilLine className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
            {t("startTest")}
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      <Card>
        <CardHeader className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <CardTitle className="text-2xl font-bold">{t("title")}</CardTitle>
            <p className="text-sm text-muted-foreground">{t("description")}</p>
          </div>
          <Button asChild className="text-white">
            <Link href={PATHS.STUDY.DETERMINE_LEVEL.START}>
              <PencilLine className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
              {t("retakeTest")}
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          <div className="mb-6 flex flex-col justify-between gap-4 rounded-lg border bg-card p-4 md:flex-row md:items-center">
            <h3 className="text-lg font-semibold">{t("attemptsLogTitle")}</h3>
            <div className="flex items-center gap-2">
              <ListFilter className="h-5 w-5 text-muted-foreground" />
              <Select
                value={sortBy}
                onValueChange={(value: "date" | "percentage") =>
                  setSortBy(value)
                }
                dir={document.documentElement.dir as "rtl" | "ltr"}
              >
                <SelectTrigger className="w-[180px]">
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

          {/* Desktop Table */}
          <div className="hidden md:block">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="rtl:text-right">
                    {t("attemptsTable.date")}
                  </TableHead>
                  <TableHead className="text-center">
                    {t("attemptsTable.numQuestions")}
                  </TableHead>
                  <TableHead className="text-center">
                    {t("attemptsTable.percentage")}
                  </TableHead>
                  <TableHead className="rtl:text-right">
                    {t("attemptsTable.quantitativePerformance")}
                  </TableHead>
                  <TableHead className="rtl:text-right">
                    {t("attemptsTable.verbalPerformance")}
                  </TableHead>
                  <TableHead className="text-center">
                    {t("attemptsTable.status")}
                  </TableHead>
                  <TableHead className="w-[280px] text-center">
                    {t("attemptsTable.actions")}
                  </TableHead>{" "}
                  {/* Adjusted width for actions */}
                </TableRow>
              </TableHeader>
              <TableBody>
                {attempts.map((attempt) => (
                  <TableRow key={attempt.attempt_id}>
                    <TableCell>
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
                    <TableCell>
                      <span
                        className={cn(
                          "px-2 py-1 rounded-md text-xs font-medium",
                          getBadgeStyle(attempt.quantitative_level_display)
                        )}
                      >
                        {attempt.quantitative_level_display ||
                          tBadge("default")}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          "px-2 py-1 rounded-md text-xs font-medium",
                          getBadgeStyle(attempt.verbal_level_display)
                        )}
                      >
                        {attempt.verbal_level_display || tBadge("default")}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span
                        className={`px-2 py-1 rounded-md text-xs font-medium ${
                          attempt.status === "completed"
                            ? "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100"
                            : attempt.status === "started"
                            ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-700 dark:text-yellow-100"
                            : "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100" // for 'abandoned' or other
                        }`}
                      >
                        {attempt.status_display || attempt.status}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      {renderActionButtons(attempt)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile Accordion */}
          <div className="space-y-3 md:hidden">
            <Accordion type="single" collapsible className="w-full">
              {attempts.map((attempt) => (
                <AccordionItem
                  value={`item-${attempt.attempt_id}`}
                  key={attempt.attempt_id}
                  className="rounded-lg border dark:border-gray-700"
                >
                  <AccordionTrigger className="p-4 hover:no-underline">
                    <div className="flex w-full items-center justify-between">
                      <div className="text-start rtl:text-right">
                        <p className="font-medium">
                          {new Date(attempt.date).toLocaleDateString(
                            undefined,
                            {
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                            }
                          )}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {t("attemptsTable.percentage")}:{" "}
                          {attempt.score_percentage !== null
                            ? `${attempt.score_percentage.toFixed(0)}%`
                            : attempt.status === "started"
                            ? t("attemptsTable.statusInProgress")
                            : "-"}
                        </p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded-md text-xs font-medium ${
                          attempt.status === "completed"
                            ? "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100"
                            : attempt.status === "started"
                            ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-700 dark:text-yellow-100"
                            : "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100"
                        } me-2 rtl:ms-2 rtl:me-0`}
                      >
                        {attempt.status_display || attempt.status}
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="p-4 pt-0">
                    <div className="space-y-2 text-sm">
                      <p>
                        <strong>{t("attemptsTable.numQuestions")}:</strong>{" "}
                        {attempt.num_questions}
                      </p>
                      <p>
                        <strong>
                          {t("attemptsTable.quantitativePerformance")}:
                        </strong>{" "}
                        <span
                          className={cn(
                            "px-2 py-1 rounded-md text-xs",
                            getBadgeStyle(attempt.quantitative_level_display)
                          )}
                        >
                          {attempt.quantitative_level_display ||
                            tBadge("default")}
                        </span>
                      </p>
                      <p>
                        <strong>{t("attemptsTable.verbalPerformance")}:</strong>{" "}
                        <span
                          className={cn(
                            "px-2 py-1 rounded-md text-xs",
                            getBadgeStyle(attempt.verbal_level_display)
                          )}
                        >
                          {attempt.verbal_level_display || tBadge("default")}
                        </span>
                      </p>
                      <div className="mt-3">{renderActionButtons(attempt)}</div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const DetermineLevelPageSkeleton = () => {
  const t = useTranslations("Study.determineLevel");
  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      <Card>
        <CardHeader className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <Skeleton className="mb-2 h-8 w-48" />
            <Skeleton className="h-4 w-72" />
          </div>
          <Skeleton className="h-10 w-48" />
        </CardHeader>
        <CardContent>
          <div className="mb-6 flex flex-col justify-between gap-4 rounded-lg border bg-background p-4 md:flex-row md:items-center">
            <Skeleton className="h-7 w-40" />
            <Skeleton className="h-10 w-[180px]" />
          </div>

          {/* Desktop Table Skeleton */}
          <div className="hidden md:block">
            <Table>
              <TableHeader>
                <TableRow>
                  {[...Array(6)].map((_, i) => (
                    <TableHead key={i}>
                      <Skeleton className="h-5 w-24" />
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {[...Array(3)].map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Skeleton className="h-5 w-20" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="inline-block h-5 w-10" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="inline-block h-5 w-10" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-6 w-16" />
                    </TableCell>
                    <TableCell>
                      <Skeleton className="h-6 w-16" />
                    </TableCell>
                    <TableCell className="text-center">
                      <Skeleton className="h-9 w-32" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile Accordion Skeleton */}
          <div className="space-y-3 md:hidden">
            <Accordion type="single" collapsible className="w-full">
              {[...Array(3)].map((_, i) => (
                <AccordionItem
                  value={`item-skeleton-${i}`}
                  key={`skeleton-${i}`}
                  className="rounded-lg border dark:border-gray-700"
                >
                  <AccordionTrigger className="p-4 hover:no-underline">
                    <div className="flex w-full items-center justify-between">
                      <div className="text-start rtl:text-right">
                        <Skeleton className="mb-1 h-5 w-24" />
                        <Skeleton className="h-4 w-32" />
                      </div>
                      <Skeleton className="h-6 w-6" />{" "}
                      {/* Chevron placeholder */}
                    </div>
                  </AccordionTrigger>
                  {/* No need to skeletonize AccordionContent as it's hidden by default */}
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LevelAssessmentPage;
