"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { PencilLine, ListXIcon, ChevronDown } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import {
  getTestAttempts,
  retakeTestAttempt,
  cancelTestAttempt,
} from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import {
  PaginatedUserTestAttempts,
  UserTestAttemptStartResponse,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { toast } from "sonner";
import TestAttemptsList from "@/components/features/platform/study/tests/TestAttemptsList";
import { queryKeys } from "@/constants/queryKeys";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { DropdownMenuTrigger } from "@radix-ui/react-dropdown-menu";
import { Switch } from "@/components/ui/switch";

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger);

const PAGE_SIZE = 20;

const TestsPage = () => {
  const t = useTranslations("Study.tests");
  const tOptions = useTranslations("Study.tests.list.sortByOptions");
  const tActions = useTranslations("Study.tests.list.actions");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [retakingId, setRetakingId] = useState<number | null>(null);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [poorTests, setPoorTests] = useState(false);
  const [selectedSort, setSelectedSort] = useState<"dateDesc" | "dateAsc">(
    "dateDesc"
  );
  const { locale } = useParams();
  const dir = locale === "en" ? "ltr" : "rtl";

  // Refs for GSAP animations
  const containerRef = useRef<HTMLDivElement>(null);
  const headerCardRef = useRef<HTMLDivElement>(null);
  const tableCardRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const buttonRef = useRef<HTMLAnchorElement>(null);
  const controlsRef:any = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<gsap.core.Timeline | null>(null);

  const { data, isLoading, isFetching, error } = useQuery<
    PaginatedUserTestAttempts,
    Error
  >({
    queryKey: queryKeys.tests.list({ types: ["practice", "simulation"], page }),
    queryFn: () =>
      getTestAttempts({
        attempt_type__in: "practice,simulation",
        page,
        ordering: "-date",
      }),
  });

  const retakeMutation = useMutation<
    UserTestAttemptStartResponse,
    Error,
    number
  >({
    mutationFn: retakeTestAttempt,
    onMutate: (attemptId) => {
      setRetakingId(attemptId);
      // Animate button loading state
      if (buttonRef.current) {
        gsap.to(buttonRef.current, {
          scale: 0.95,
          duration: 0.1,
          yoyo: true,
          repeat: 1,
        });
      }
    },
    onSuccess: (data) => {
      toast.success(t("api.retakeSuccess"));
      // Success animation
      gsap.fromTo(
        containerRef.current,
        { x: 0 },
        { 
          x: dir === "rtl" ? 20 : -20, 
          duration: 0.3, 
          yoyo: true, 
          repeat: 1,
          ease: "power2.out"
        }
      );
      router.push(PATHS.STUDY.TESTS.ATTEMPT(data.attempt_id));
    },
    onError: (err: any) => {
      toast.error(getApiErrorMessage(err, tCommon("errors.generic")));
      // Error shake animation
      gsap.fromTo(
        containerRef.current,
        { x: 0 },
        { 
          x: 10, 
          duration: 0.1, 
          yoyo: true, 
          repeat: 5,
          ease: "power2.out"
        }
      );
    },
    onSettled: () => setRetakingId(null),
  });

  const cancelAttemptMutation = useMutation<void, Error, number>({
    mutationFn: cancelTestAttempt,
    onMutate: (attemptId) => setCancellingId(attemptId),
    onSuccess: (_, attemptId) => {
      toast.success(tActions("cancelDialog.successToast", { attemptId }));
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
      
      // Success pulse animation
      gsap.fromTo(
        tableCardRef.current,
        { scale: 1 },
        { 
          scale: 1.02, 
          duration: 0.2, 
          yoyo: true, 
          repeat: 1,
          ease: "power2.out"
        }
      );
    },
    onError: (err: any) => {
      toast.error(
        getApiErrorMessage(err, tActions("cancelDialog.errorToastGeneric"))
      );
    },
    onSettled: () => setCancellingId(null),
  });

  const { attempts, pageCount, canPreviousPage, canNextPage } = useMemo(() => {
    const results = data?.results ?? [];

    const filtered = poorTests
      ? results.filter(
          (attempt) =>
            attempt.score_percentage !== null && attempt.score_percentage < 50
        )
      : results;

    const sorted = [...filtered].sort((a, b) => {
      switch (selectedSort) {
        case "dateAsc":
          return new Date(a.date).getTime() - new Date(b.date).getTime();
        case "dateDesc":
          return new Date(b.date).getTime() - new Date(a.date).getTime();
        default:
          return 0;
      }
    });
    return {
      attempts: sorted ?? [],
      pageCount: data?.count ? Math.ceil(data.count / PAGE_SIZE) : 1,
      canPreviousPage: !!data?.previous,
      canNextPage: !!data?.next,
    };
  }, [data?.results, page, poorTests, selectedSort]);

  // Initial page load animations
  useEffect(() => {
    if (!isLoading && containerRef.current) {
      // Create timeline for coordinated animations
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
      timelineRef.current = tl;

      // Set initial states
      gsap.set([headerCardRef.current, tableCardRef.current], { 
        opacity: 0, 
        y: 50 
      });
      gsap.set(titleRef.current, { 
        opacity: 0, 
        x: dir === "rtl" ? -30 : 30 
      });
      gsap.set(buttonRef.current, { 
        opacity: 0, 
        scale: 0.8 
      });
      gsap.set(controlsRef.current, { 
        opacity: 0, 
        y: 20 
      });

      // Animate in sequence
      tl.to(headerCardRef.current, { 
        opacity: 1, 
        y: 0, 
        duration: 0.6 
      })
        .to(titleRef.current, { 
          opacity: 1, 
          x: 0, 
          duration: 0.5 
        }, "-=0.3")
        .to(buttonRef.current, { 
          opacity: 1, 
          scale: 1, 
          duration: 0.4 
        }, "-=0.2")
        .to(tableCardRef.current, { 
          opacity: 1, 
          y: 0, 
          duration: 0.6 
        }, "-=0.3")
        .to(controlsRef.current, { 
          opacity: 1, 
          y: 0, 
          duration: 0.4 
        }, "-=0.4");

      // Add scroll-triggered animations for table content
      if (attempts.length > 0) {
        ScrollTrigger.create({
          trigger: tableCardRef.current,
          start: "top 80%",
          onEnter: () => {
            gsap.fromTo(
              ".test-attempt-item", 
              { 
                opacity: 0, 
                x: dir === "rtl" ? -20 : 20 
              },
              { 
                opacity: 1, 
                x: 0, 
                duration: 0.4, 
                stagger: 0.1,
                ease: "power2.out"
              }
            );
          }
        });
      }

      return () => {
        ScrollTrigger.getAll().forEach(trigger => trigger.kill());
        if (timelineRef.current) {
          timelineRef.current.kill();
        }
      };
    }
  }, [isLoading, attempts.length, dir]);

  // Animate filter/sort changes
  useEffect(() => {
    if (!isLoading && tableCardRef.current) {
      gsap.fromTo(
        tableCardRef.current.querySelector('.card-content'),
        { opacity: 0.7, y: 10 },
        { 
          opacity: 1, 
          y: 0, 
          duration: 0.3,
          ease: "power2.out"
        }
      );
    }
  }, [attempts, poorTests, selectedSort]);

  const handleRetake = (attemptId: number) => {
    retakeMutation.mutate(attemptId);
  };

  const handleSortChange = (newSort: "dateDesc" | "dateAsc") => {
    // Animate sort change
    if (controlsRef.current) {
      gsap.to(controlsRef.current, {
        scale: 1.05,
        duration: 0.1,
        yoyo: true,
        repeat: 1,
      });
    }
    setSelectedSort(newSort);
  };

  const handlePoorTestsToggle = () => {
    // Animate toggle
    gsap.to(controlsRef.current?.querySelector('[role="switch"]'), {
      scale: 1.1,
      duration: 0.1,
      yoyo: true,
      repeat: 1,
    });
    setPoorTests(!poorTests);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
        <Card>
          <CardHeader className="flex flex-col items-start justify-between md:flex-row md:items-center">
            <div className="flex-1">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="mt-2 h-4 w-72" />
            </div>
            <Skeleton className="mt-4 h-12 w-44 md:mt-0" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <Alert variant="destructive">
          <AlertTitle>{tCommon("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(error, tCommon("errors.generic"))}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const hasNoAttemptsAtAll = !data?.count;

  return (
    <div 
      ref={containerRef}
      className="container mx-auto space-y-6 p-4 sm:p-6 lg:p-8"
    >
      <Card ref={headerCardRef} dir={dir}>
        <CardHeader className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div className="w-full">
            <CardTitle 
              ref={titleRef}
              className="flex items-center text-center justify-center sm:justify-start text-2xl mb-2 font-bold"
            >
              {t("simulationTest.title")}
            </CardTitle>
            <p className="mt-1 text-muted-foreground">
              <span className="w-1 h-1 rounded-full bg-current me-2 inline-block" />
              {t("simulationTest.retakeDescription")}
            </p>
            <p className="mt-1 text-muted-foreground">
              <span className="w-1 h-1 rounded-full bg-current me-2 inline-block" />
              {t("simulationTest.reviewDescription")}
            </p>
          </div>
          <Button 
            asChild 
            size="lg" 
            className="self-center transition-transform hover:scale-105"
          >
            <Link ref={buttonRef} href={PATHS.STUDY.TESTS.START}>
              <PencilLine className="me-2 h-5 w-5" />
              {t("list.startNewTest")}
            </Link>
          </Button>
        </CardHeader>
      </Card>

      {/* Table Card */}
      <Card ref={tableCardRef} dir={dir}>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between w-full">
            <div className="flex flex-col sm:flex-row md:w-full">
              <CardTitle className="text-xl font-bold text-center sm:text-right mb-2 min-w-36">
                {t("list.title")}
              </CardTitle>
              <div 
                ref={controlsRef}
                className="flex items-center justify-between md:justify-end w-full gap-4"
              >
                <div className="flex items-center gap-2">
                  {t("list.showLowPerformanceTests")}
                  <Switch
                    onClick={handlePoorTestsToggle}
                    className="transition-transform hover:scale-110"
                  />
                </div>
                <div className="flex items-center flex-col md:flex-row gap-2">
                  <span className="text-sm">{t("list.sortBy")}</span>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="outline"
                        className="transition-transform hover:scale-105"
                      >
                        {tOptions(selectedSort)}
                        <ChevronDown className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent className="text-center">
                      <DropdownMenuItem
                        className="justify-center transition-colors hover:bg-accent"
                        onSelect={() => handleSortChange("dateDesc")}
                      >
                        {tOptions("dateDesc")}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="justify-center transition-colors hover:bg-accent"
                        onSelect={() => handleSortChange("dateAsc")}
                      >
                        {tOptions("dateAsc")}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="card-content">
          {hasNoAttemptsAtAll ? (
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed py-6 text-center">
              <ListXIcon size={48} className="text-primary animate-pulse" />
              <h3 className="mt-4 text-xl font-semibold">
                لا يوجد امتحانات
              </h3>
              <p className="mt-1 text-muted-foreground">
                يجب عليك أن تأخذ امتحانًا
              </p>
            </div>
          ) : (
            <>
              <div className="test-attempts-container">
                <TestAttemptsList
                  attempts={attempts}
                  onRetake={handleRetake}
                  isRetaking={retakeMutation.isPending}
                  retakeAttemptId={retakingId}
                  cancelAttemptMutation={cancelAttemptMutation}
                  cancellingAttemptId={cancellingId}
                />
              </div>
              <DataTablePagination
                page={page}
                pageCount={pageCount}
                setPage={setPage}
                canPreviousPage={canPreviousPage}
                canNextPage={canNextPage}
                isFetching={isFetching}
                className="mt-4 transition-opacity duration-300"
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TestsPage;
