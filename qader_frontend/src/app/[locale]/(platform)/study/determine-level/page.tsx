"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { PencilLine, ListFilter } from "lucide-react";
import { gsap } from "gsap";

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

  // Animation refs
  const containerRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<HTMLDivElement>(null);
  const mobileRef = useRef<HTMLDivElement>(null);
  const paginationRef = useRef<HTMLDivElement>(null);
  const noDataRef = useRef<HTMLDivElement>(null);
  const animationTimelineRef = useRef<gsap.core.Timeline | null>(null);

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

  // GSAP Animations
  useEffect(() => {
    if (isLoading) return;

    // Kill any existing timeline
    if (animationTimelineRef.current) {
      animationTimelineRef.current.kill();
    }

    // Create main timeline
    const tl = gsap.timeline({
      defaults: { ease: "power3.out" }
    });
    animationTimelineRef.current = tl;

    // Set initial states
    gsap.set([cardRef.current], { 
      opacity: 0, 
      y: 30,
      scale: 0.95
    });

    if (headerRef.current) {
      gsap.set(headerRef.current.children, { 
        opacity: 0, 
        x: -20 
      });
    }

    if (controlsRef.current) {
      gsap.set(controlsRef.current, { 
        opacity: 0, 
        y: 20 
      });
    }

    // Main card animation
    tl.to(cardRef.current, {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.6,
      ease: "back.out(1.7)"
    });

    // Header content animation
    if (headerRef.current) {
      tl.to(headerRef.current.children, {
        opacity: 1,
        x: 0,
        duration: 0.4,
        stagger: 0.1,
        ease: "power2.out"
      }, "-=0.3");
    }

    // Controls animation
    if (controlsRef.current) {
      tl.to(controlsRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.4
      }, "-=0.2");
    }

    // Table rows animation (desktop)
    if (tableRef.current) {
      const rows = tableRef.current.querySelectorAll("tbody tr");
      gsap.set(rows, { opacity: 0, x: -30 });
      
      tl.to(rows, {
        opacity: 1,
        x: 0,
        duration: 0.3,
        stagger: 0.05,
        ease: "power2.out"
      }, "-=0.1");

      // Add hover animations to rows
      rows.forEach((row) => {
        row.addEventListener("mouseenter", () => {
          gsap.to(row, {
            scale: 1.02,
            backgroundColor: "rgba(59, 130, 246, 0.05)",
            duration: 0.2,
            ease: "power2.out"
          });
        });

        row.addEventListener("mouseleave", () => {
          gsap.to(row, {
            scale: 1,
            backgroundColor: "transparent",
            duration: 0.2,
            ease: "power2.out"
          });
        });
      });
    }

    // Mobile accordion animation
    if (mobileRef.current) {
      const items = mobileRef.current.querySelectorAll("[data-state]");
      gsap.set(items, { opacity: 0, y: 20 });
      
      tl.to(items, {
        opacity: 1,
        y: 0,
        duration: 0.3,
        stagger: 0.08,
        ease: "power2.out"
      }, "-=0.1");
    }

    // Pagination animation
    if (paginationRef.current) {
      gsap.set(paginationRef.current, { opacity: 0, y: 20 });
      tl.to(paginationRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.4
      });
    }

    // Cleanup
    return () => {
      if (animationTimelineRef.current) {
        animationTimelineRef.current.kill();
      }
    };
  }, [isLoading, attempts, page]);

  // No data animation
  useEffect(() => {
    if (!attemptsData?.count && noDataRef.current) {
      const tl = gsap.timeline();
      
      const img = noDataRef.current.querySelector("img");
      const texts = noDataRef.current.querySelectorAll("h2, p, button");
      
      gsap.set([img, texts], { opacity: 0 });
      gsap.set(img, { scale: 0.5, rotation: -10 });
      gsap.set(texts, { y: 30 });
      
      tl.to(img, {
        opacity: 1,
        scale: 1,
        rotation: 0,
        duration: 0.8,
        ease: "back.out(1.7)"
      })
      .to(texts, {
        opacity: 1,
        y: 0,
        duration: 0.5,
        stagger: 0.1,
        ease: "power3.out"
      }, "-=0.4");

      // Floating animation for image
      gsap.to(img, {
        y: -10,
        duration: 2,
        repeat: -1,
        yoyo: true,
        ease: "power1.inOut"
      });
    }
  }, [attemptsData?.count]);

  // Badge animation on hover
  useEffect(() => {
    const badges = document.querySelectorAll("span[class*='rounded-md']");
    badges.forEach((badge) => {
      badge.addEventListener("mouseenter", () => {
        gsap.to(badge, {
          scale: 1.1,
          duration: 0.2,
          ease: "power2.out"
        });
      });

      badge.addEventListener("mouseleave", () => {
        gsap.to(badge, {
          scale: 1,
          duration: 0.2,
          ease: "power2.out"
        });
      });
    });
  }, [attempts]);

  const handleSortChange = (value: "date" | "percentage") => {
    // Animate the sort change
    gsap.to([tableRef.current, mobileRef.current], {
      opacity: 0,
      y: 10,
      duration: 0.2,
      onComplete: () => {
        setPage(1);
        setSortBy(value);
        gsap.to([tableRef.current, mobileRef.current], {
          opacity: 1,
          y: 0,
          duration: 0.3
        });
      }
    });
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
      <div ref={noDataRef} className="flex min-h-[calc(100vh-100px)] sm:min-h-[calc(100vh-150px)] flex-col items-center justify-center p-4 text-center">
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
    <div ref={containerRef} className="container mx-auto space-y-4 sm:space-y-6 p-3 sm:p-4 md:p-6 lg:p-8 max-w-7xl">
      <Card ref={cardRef} className="dark:bg-[#0B1739] dark:border-[#7E89AC] border-2">
        <CardHeader 
          ref={headerRef}
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
          <div ref={controlsRef} className="mb-4 sm:mb-6 flex flex-col justify-between gap-3 sm:gap-4 rounded-lg border bg-card p-3 sm:p-4 sm:flex-row sm:items-center dark:bg-[#0B1739]">
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
          <div ref={tableRef} className="hidden rounded-xl border overflow-x-auto md:block">
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
                          "inline-block rounded-md px-1.5 py-0.5 sm:px-2 sm:py-1 text-xs font-medium transition-transform",
                          getBadgeStyle(attempt.quantitative_level_key)
                        )}
                      >
                        {tBadge(attempt.quantitative_level_key)}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span
                        className={cn(
                          "inline-block rounded-md px-1.5 py-0.5 sm:px-2 sm:py-1 text-xs font-medium transition-transform",
                          getBadgeStyle(attempt.verbal_level_key)
                        )}
                      >
                        {tBadge(attempt.verbal_level_key)}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <span
                        className={cn(
                          "inline-block rounded-md px-1.5 py-0.5 sm:px-2 sm:py-1 text-xs font-medium transition-transform",
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
          <div ref={mobileRef} className="space-y-2 sm:space-y-3 md:hidden">
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
          <div ref={paginationRef}>
            <DataTablePagination
              page={page}
              pageCount={pageCount}
              setPage={setPage}
              canPreviousPage={canPreviousPage}
              canNextPage={canNextPage}
              isFetching={isFetching}
              className="mt-4"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Responsive Skeleton component
const DetermineLevelPageSkeleton = () => {
  const skeletonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (skeletonRef.current) {
      const elements = skeletonRef.current.querySelectorAll(".animate-pulse");
      gsap.fromTo(elements, 
        { opacity: 0.3 },
        { 
          opacity: 1, 
          duration: 1.5, 
          repeat: -1, 
          yoyo: true,
          stagger: 0.1,
          ease: "power1.inOut"
        }
      );
    }
  }, []);

  return (
    <div ref={skeletonRef} className="container mx-auto space-y-4 sm:space-y-6 p-3 sm:p-4 md:p-6 lg:p-8 max-w-7xl">
      <Card>
        <CardHeader className="flex flex-col justify-between gap-3 sm:gap-4 p-4 sm:p-6 md:flex-row md:items-center">
          <div>
            <Skeleton className="mb-2 h-6 sm:h-8 w-32 sm:w-48 animate-pulse" />
            <Skeleton className="h-3 sm:h-4 w-48 sm:w-72 animate-pulse" />
          </div>
          <Skeleton className="h-9 sm:h-10 w-full sm:w-48 animate-pulse" />
        </CardHeader>
        <CardContent className="p-3 sm:p-4 md:p-6">
          <div className="mb-4 sm:mb-6 flex flex-col justify-between gap-3 sm:gap-4 rounded-lg border bg-background p-3 sm:p-4 sm:flex-row sm:items-center">
            <Skeleton className="h-5 sm:h-7 w-32 sm:w-40 animate-pulse" />
            <Skeleton className="h-9 sm:h-10 w-full sm:w-[180px] animate-pulse" />
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
