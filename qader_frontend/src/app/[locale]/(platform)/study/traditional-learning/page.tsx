"use client";

import React, { useState, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { ListFilter, Sparkles, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
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
import { toast } from "sonner";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { cn } from "@/lib/utils";

import { getTestAttempts, cancelTestAttempt } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PaginatedUserTestAttempts } from "@/types/api/study.types";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import TraditionalLearningConfigForm from "@/components/features/platform/study/traditional-learning/TraditionalLearningConfigForm";
import { AttemptActionButtons } from "./_components/AttemptActionButtons";

const PAGE_SIZE = 20;

export default function TraditionalLearningHubPage() {
  const t = useTranslations("Study.traditionalLearning.list");
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<"date">("date"); // Only date sorting for now

  const {
    data: attemptsData,
    isLoading,
    isFetching,
    error,
  } = useQuery<PaginatedUserTestAttempts, Error>({
    queryKey: [
      QUERY_KEYS.USER_TEST_ATTEMPTS,
      { attempt_type: "traditional", page, ordering: "-date" },
    ],
    queryFn: () =>
      getTestAttempts({
        attempt_type: "traditional",
        page,
        ordering: "-date",
      }),
  });

  const cancelAttemptMutation = useMutation({
    mutationFn: cancelTestAttempt,
    onSuccess: (_, attemptId) => {
      toast.success(t("actions.cancelDialog.successToast", { attemptId }));
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPTS],
      });
    },
    onError: (err) => {
      toast.error(
        getApiErrorMessage(err, t("actions.cancelDialog.errorToastGeneric"))
      );
    },
  });

  const { attempts, pageCount, canPreviousPage, canNextPage } = useMemo(() => {
    const results = attemptsData?.results ?? [];
    return {
      attempts: results,
      pageCount: attemptsData?.count
        ? Math.ceil(attemptsData.count / PAGE_SIZE)
        : 1,
      canPreviousPage: !!attemptsData?.previous,
      canNextPage: !!attemptsData?.next,
    };
  }, [attemptsData]);

  if (isLoading) {
    return <TraditionalLearningPageSkeleton />;
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

  const hasAttempts = (attemptsData?.count ?? 0) > 0;

  return (
    <div className="container mx-auto space-y-8 p-4 md:p-6 lg:p-8">
      {/* Configuration Form is always visible */}
      <TraditionalLearningConfigForm />

      {/* Attempts List, only shown if there are attempts */}
      {hasAttempts && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <History className="h-6 w-6 text-primary" />
              <CardTitle>{t("attemptsLogTitle")}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {/* Desktop Table */}
            <div className="hidden rounded-xl border md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("table.date")}</TableHead>
                    <TableHead className="text-center">
                      {t("table.numQuestions")}
                    </TableHead>
                    <TableHead className="text-center">
                      {t("table.status")}
                    </TableHead>
                    <TableHead className="w-[180px] text-center">
                      {t("table.actions")}
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
                      <TableCell>
                        {new Date(attempt.date).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-center">
                        {attempt.num_questions}
                      </TableCell>
                      <TableCell className="text-center">
                        <span
                          className={cn(
                            "rounded-md px-2 py-1 text-xs font-medium",
                            {
                              "bg-yellow-100 text-yellow-700 dark:bg-yellow-700 dark:text-yellow-100":
                                attempt.status === "started",
                              "bg-green-100 text-green-700 dark:bg-green-700 dark:text-green-100":
                                attempt.status === "completed",
                              "bg-red-100 text-red-700 dark:bg-red-700 dark:text-red-100":
                                attempt.status === "abandoned",
                            }
                          )}
                        >
                          {attempt.status_display}
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

            {/* Mobile Accordion */}
            <div className="space-y-3 md:hidden">
              <Accordion type="single" collapsible className="w-full">
                {attempts.map((attempt) => (
                  <AccordionItem
                    value={`item-${attempt.attempt_id}`}
                    key={attempt.attempt_id}
                    className="rounded-lg border"
                  >
                    <AccordionTrigger className="p-4 hover:no-underline">
                      <div className="flex w-full items-center justify-between">
                        <p className="font-medium">
                          {new Date(attempt.date).toLocaleDateString()}
                        </p>
                        <span
                          className={cn(
                            "me-2 rounded-md px-2 py-1 text-xs font-medium rtl:ms-2 rtl:me-0",
                            {
                              "bg-yellow-100 text-yellow-700":
                                attempt.status === "started",
                              "bg-green-100 text-green-700":
                                attempt.status === "completed",
                              "bg-red-100 text-red-700":
                                attempt.status === "abandoned",
                            }
                          )}
                        >
                          {attempt.status_display}
                        </span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="p-4 pt-0">
                      <div className="space-y-3">
                        <p>
                          <strong>{t("table.numQuestions")}:</strong>{" "}
                          {attempt.num_questions}
                        </p>
                        <AttemptActionButtons
                          attempt={attempt}
                          cancelAttemptMutation={cancelAttemptMutation}
                        />
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>

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
      )}

      {!hasAttempts && !isLoading && (
        <div className="rounded-lg border-2 border-dashed p-8 text-center text-muted-foreground">
          <History className="mx-auto mb-4 h-12 w-12" />
          <h3 className="mb-2 text-xl font-semibold">{t("noAttemptsTitle")}</h3>
          <p>{t("noAttemptsDescription")}</p>
        </div>
      )}
    </div>
  );
}

// Skeleton remains in the same file for simplicity
const TraditionalLearningPageSkeleton = () => (
  <div className="container mx-auto space-y-8 p-4 md:p-6 lg:p-8">
    {/* Config Form Skeleton */}
    <div className="mx-auto max-w-4xl space-y-8">
      <Skeleton className="h-[200px] w-full" />
      <Skeleton className="h-[300px] w-full" />
      <div className="flex justify-end">
        <Skeleton className="h-12 w-48" />
      </div>
    </div>

    {/* Attempts List Skeleton */}
    <Card>
      <CardHeader>
        <Skeleton className="h-8 w-48" />
      </CardHeader>
      <CardContent>
        <div className="hidden rounded-xl border md:block">
          <Table>
            <TableHeader>
              <TableRow>
                {[...Array(4)].map((_, i) => (
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
                    <Skeleton className="h-5 w-32" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="mx-auto h-5 w-16" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="mx-auto h-6 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="mx-auto h-9 w-32" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-9 w-24" />
        </div>
      </CardContent>
    </Card>
  </div>
);
