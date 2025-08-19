"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { History } from "lucide-react";
import { gsap } from "gsap";

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
import { PaginatedUserTestAttempts } from "@/types/api/study.types";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import TraditionalLearningConfigForm from "@/components/features/platform/study/traditional-learning/TraditionalLearningConfigForm";
import { AttemptActionButtons } from "./_components/AttemptActionButtons";
import { queryKeys } from "@/constants/queryKeys";

const PAGE_SIZE = 20;

export default function TraditionalLearningHubPage() {
  const t = useTranslations("Study.traditionalLearning.list");
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);

  // Refs for GSAP animations
  const containerRef:any = useRef<HTMLDivElement>(null);
  const configFormRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const {
    data: attemptsData,
    isLoading,
    isFetching,
    error,
  } = useQuery<PaginatedUserTestAttempts, Error>({
    queryKey: queryKeys.tests.list({
      attempt_type: "traditional",
      page,
      ordering: "-date",
    }),
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
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
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

  // GSAP Animation Effect
  useEffect(() => {
    if (!containerRef.current) return;

    // Create GSAP context for cleanup
    const ctx = gsap.context(() => {
      // Timeline for sequential animations
      const tl = gsap.timeline({
        defaults: {
          ease: "power3.out",
          duration: 0.8,
        }
      });

      // Set initial states
      gsap.set([configFormRef.current, contentRef.current], {
        opacity: 0,
        y: 30,
      });

      // Animate sections in sequence
      tl.to(configFormRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.6,
      })
      .to(contentRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.6,
      }, "-=0.3"); // Start slightly before previous animation ends

      // Additional animation for table rows or accordion items when they load
      if (!isLoading && attempts.length > 0) {
        const items = containerRef.current.querySelectorAll(
          ".animate-row, .accordion-item"
        );
        
        gsap.fromTo(
          items,
          {
            opacity: 0,
            x: -20,
          },
          {
            opacity: 1,
            x: 0,
            duration: 0.4,
            stagger: 0.05, // Stagger each item by 50ms
            delay: 0.8, // Wait for main sections to animate
            ease: "power2.out",
          }
        );
      }
    }, containerRef);

    // Cleanup function
    return () => ctx.revert();
  }, [isLoading, attempts]);

  const renderContent = () => {
    if (isLoading) {
      return <TraditionalLearningPageSkeleton />;
    }

    if (error) {
      return (
        <Alert variant="destructive" className="mt-8 animate-fade-in">
          <AlertTitle>{t("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(error, t("errors.fetchFailedDescription"))}
          </AlertDescription>
        </Alert>
      );
    }
    
    const hasAttempts = (attemptsData?.count ?? 0) > 0;

    if (!hasAttempts) {
      return (
        <div className="mt-8 rounded-lg border-2 border-dashed p-8 text-center text-muted-foreground animate-fade-in">
          <History className="mx-auto mb-4 h-12 w-12" />
          <h3 className="mb-2 text-xl font-semibold">{t("noAttemptsTitle")}</h3>
          <p>{t("noAttemptsDescription")}</p>
        </div>
      );
    }

    return (
      <Card className="mt-8">
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
                  <TableHead className="w-[200px] text-center">
                    {t("table.actions")}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {attempts.map((attempt, index) => (
                  <TableRow
                    key={attempt.attempt_id}
                    className={cn(
                      "animate-row", // Add class for GSAP targeting
                      {
                        "opacity-60": attempt.status === "abandoned",
                      }
                    )}
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
                            "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300":
                              attempt.status === "started",
                            "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300":
                              attempt.status === "completed",
                            "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300":
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
              {attempts.map((attempt, index) => (
                <AccordionItem
                  value={`item-${attempt.attempt_id}`}
                  key={attempt.attempt_id}
                  className="accordion-item rounded-lg border" // Add class for GSAP targeting
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
                            "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300":
                              attempt.status === "started",
                            "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300":
                              attempt.status === "completed",
                            "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300":
                              attempt.status === "abandoned",
                          }
                        )}
                      >
                        {attempt.status_display}
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="p-4 pt-0">
                    <div className="space-y-4">
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
    );
  };

  return (
    <div 
      ref={containerRef}
      className="container mx-auto space-y-8 p-4 md:p-6 lg:p-8"
    >
      <div ref={configFormRef}>
        <TraditionalLearningConfigForm />
      </div>
      <div ref={contentRef}>
        {renderContent()}
      </div>
    </div>
  );
}

// Skeleton component remains the same
const TraditionalLearningPageSkeleton = () => (
  <div className="space-y-8">
    {/* Config Form Skeleton */}
    <div className="mx-auto max-w-4xl space-y-8">
      <Skeleton className="h-[250px] w-full" />
      <Skeleton className="h-[350px] w-full" />
      <div className="flex justify-end">
        <Skeleton className="h-12 w-48" />
      </div>
    </div>

    {/* Attempts List Skeleton */}
    <Card className="mt-8">
      <CardHeader>
        <Skeleton className="h-8 w-48" />
      </CardHeader>
      <CardContent>
        <div className="rounded-xl border">
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
              {[...Array(5)].map((_, i) => (
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
                    <div className="flex justify-center gap-2">
                      <Skeleton className="h-9 w-24" />
                      <Skeleton className="h-9 w-24" />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <Skeleton className="h-9 w-32" />
          <div className="flex gap-2">
            <Skeleton className="h-9 w-20" />
            <Skeleton className="h-9 w-20" />
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
);
