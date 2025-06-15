// src/app/[locale]/(platform)/study/tests/page.tsx
"use client";

import React, { useState, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { PlusCircle, ListChecks, ListXIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { DataTablePagination } from "@/components/shared/DataTablePagination";
import { getTestAttempts, retakeTestAttempt } from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import {
  PaginatedUserTestAttempts,
  UserTestAttemptStartResponse,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { toast } from "sonner";
import TestAttemptsList from "@/components/features/platform/study/tests/TestAttemptsList";
import { useRouter } from "next/navigation";

const PAGE_SIZE = 10;

const TestsPage = () => {
  const t = useTranslations("Study.tests.list");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [retakingId, setRetakingId] = useState<number | null>(null);

  const { data, isLoading, isFetching, error } = useQuery<
    PaginatedUserTestAttempts,
    Error
  >({
    queryKey: [
      QUERY_KEYS.USER_TEST_ATTEMPTS,
      { types: ["practice", "simulation"], page },
    ],
    queryFn: () =>
      getTestAttempts({
        attempt_type__in: "practice,simulation",
        page,
        ordering: "-date",
      }),
  });

  // +++ FIX: Explicitly type the useMutation hook +++
  const retakeMutation = useMutation<
    UserTestAttemptStartResponse,
    Error,
    number
  >({
    mutationFn: retakeTestAttempt,
    onMutate: (attemptId) => {
      // `attemptId` is now correctly inferred as `number`, matching the state type.
      setRetakingId(attemptId);
    },
    onSuccess: (data) => {
      toast.success(t("api.retakeSuccess"));
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPTS],
      });
      router.push(PATHS.STUDY.TESTS.ATTEMPT(data.attempt_id));
    },
    onError: (err: any) => {
      toast.error(getApiErrorMessage(err, tCommon("errors.generic")));
    },
    onSettled: () => {
      setRetakingId(null);
    },
  });

  const { attempts, pageCount, canPreviousPage, canNextPage } = useMemo(() => {
    const results = data?.results ?? [];
    return {
      attempts: results,
      pageCount: data?.count ? Math.ceil(data.count / PAGE_SIZE) : 1,
      canPreviousPage: !!data?.previous,
      canNextPage: !!data?.next,
    };
  }, [data]);

  const handleRetake = (attemptId: number) => {
    // This call is now type-checked against the `number` generic we provided.
    retakeMutation.mutate(attemptId);
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

  // +++ FIX: Corrected variable name typo +++
  const hasNoAttemptsAtAll = !data?.count;

  return (
    <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
      <Card>
        <CardHeader className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <CardTitle className="flex items-center text-2xl font-bold">
              <ListChecks className="me-3 h-7 w-7 text-primary" />
              {t("title")}
            </CardTitle>
            <p className="mt-1 text-muted-foreground">{t("description")}</p>
          </div>
          <Button asChild size="lg">
            <Link href={PATHS.STUDY.TESTS.START}>
              <PlusCircle className="me-2 h-5 w-5" />
              {t("startNewTest")}
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {hasNoAttemptsAtAll ? (
            <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed py-6 text-center">
              <ListXIcon size={48} className="text-primary" />
              <h3 className="mt-4 text-xl font-semibold">
                {t("noAttemptsTitle")}
              </h3>
              <p className="mt-1 text-muted-foreground">
                {t("noAttemptsDescription")}
              </p>
            </div>
          ) : (
            <>
              <TestAttemptsList
                attempts={attempts}
                onRetake={handleRetake}
                isRetaking={retakeMutation.isPending}
                retakeAttemptId={retakingId}
              />
              <DataTablePagination
                page={page}
                pageCount={pageCount}
                setPage={setPage}
                canPreviousPage={canPreviousPage}
                canNextPage={canNextPage}
                isFetching={isFetching}
                className="mt-4"
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TestsPage;
