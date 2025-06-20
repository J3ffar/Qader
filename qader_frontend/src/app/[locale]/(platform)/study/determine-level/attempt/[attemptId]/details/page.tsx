"use client";

import React, { useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { format } from "date-fns";
import {
  ArrowLeft,
  ArrowRight,
  AlertTriangle,
  Info,
  CheckCircle2,
  XCircle,
  MinusCircle,
  Hash,
  ListChecks,
} from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

import { getTestAttemptDetails } from "@/services/study.service";
import {
  UserTestAttemptDetail,
  UnifiedQuestion,
} from "@/types/api/study.types";
import { PATHS } from "@/constants/paths";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";

const LevelAssessmentDetailsPage = () => {
  const params = useParams();
  const router = useRouter();
  const t = useTranslations("Study.determineLevel.details");
  const tCommon = useTranslations("Common");
  const locale = params.locale as string;
  const attemptId = params.attemptId as string;

  const {
    data: attemptDetails,
    isLoading,
    error,
  } = useQuery<UserTestAttemptDetail, Error>({
    queryKey: queryKeys.tests.detail(attemptId),
    queryFn: () => getTestAttemptDetails(attemptId),
    enabled: !!attemptId,
  });

  // Use useMemo to create an efficient lookup map for attempted questions.
  // This avoids repeatedly searching the array inside the render loop.
  const attemptedQuestionsMap = useMemo(() => {
    if (!attemptDetails?.attempted_questions) {
      return new Map();
    }
    return new Map(
      attemptDetails.attempted_questions.map((aq) => [aq.question_id, aq])
    );
  }, [attemptDetails?.attempted_questions]);

  if (isLoading) return <DetailsPageSkeleton />;

  if (error || !attemptDetails) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert variant="destructive" className="max-w-lg">
          <AlertTriangle className="mx-auto mb-2 h-6 w-6" />
          <AlertTitle>{tCommon("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(error, t("errors.fetchDetailsFailed"))}
          </AlertDescription>
        </Alert>
        <Button
          onClick={() =>
            router.push(PATHS.STUDY.DETERMINE_LEVEL.REVIEW(attemptId))
          }
          variant="outline"
          className="mt-6"
        >
          {locale === "ar" ? (
            <ArrowRight className="me-2 h-4 w-4" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4" />
          )}
          {t("backToScorePage")}
        </Button>
      </div>
    );
  }

  const {
    status_display,
    date,
    score_verbal,
    score_quantitative,
    configuration_snapshot,
    included_questions,
  } = attemptDetails;

  return (
    <div className="container mx-auto max-w-full p-5">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="icon"
              onClick={() =>
                router.push(PATHS.STUDY.DETERMINE_LEVEL.REVIEW(attemptId))
              }
            >
              {locale === "ar" ? (
                <ArrowRight className="h-4 w-4" />
              ) : (
                <ArrowLeft className="h-4 w-4" />
              )}
              <span className="sr-only">{t("backToScorePage")}</span>
            </Button>
            <div>
              <CardTitle className="text-2xl">{t("pageTitle")}</CardTitle>
              <CardDescription>
                {tCommon("attempt")} #{attemptId}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Summary Section (No changes needed) */}
          <div>
            <h3 className="mb-4 text-lg font-semibold">{t("summaryTitle")}</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">
              <InfoCard title={t("status")} value={status_display} />
              <InfoCard
                title={t("testDate")}
                value={format(new Date(date), "PPP")}
              />
              <InfoCard
                title={t("scoreVerbal")}
                value={
                  score_verbal !== null ? `${score_verbal.toFixed(0)}%` : "N/A"
                }
              />
              <InfoCard
                title={t("scoreQuantitative")}
                value={
                  score_quantitative !== null
                    ? `${score_quantitative.toFixed(0)}%`
                    : "N/A"
                }
              />
            </div>
          </div>

          <Separator />

          {/* Configuration Section (No changes needed) */}
          {configuration_snapshot && (
            <div>
              <h3 className="mb-4 text-lg font-semibold">
                {t("configurationTitle")}
              </h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <InfoCard
                  title={t("numQuestions")}
                  value={configuration_snapshot.num_questions_requested}
                  Icon={Hash}
                />
                <InfoCard
                  title={t("numQuestionsSelected")}
                  value={configuration_snapshot.num_questions_selected}
                  Icon={Hash}
                />
                <InfoCard
                  title={t("sections")}
                  value={
                    configuration_snapshot.sections_requested?.join(", ") ||
                    "N/A"
                  }
                  Icon={ListChecks}
                />
              </div>
            </div>
          )}

          <Separator />

          {/* Answered Questions Table */}
          <div>
            <h3 className="mb-4 text-lg font-semibold">
              {t("detailedBreakdownTitle")}
            </h3>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50%] rtl:text-right">
                      {t("tableHeaderQuestion")}
                    </TableHead>
                    <TableHead className="text-center">
                      {t("tableHeaderYourAnswer")}
                    </TableHead>
                    <TableHead className="text-center">
                      {t("tableHeaderCorrectAnswer")}
                    </TableHead>
                    <TableHead className="text-center">
                      {t("tableHeaderStatus")}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {included_questions.map((question, index) => {
                    const userAttempt = attemptedQuestionsMap.get(question.id);
                    const selectedAnswer = userAttempt?.selected_answer;
                    const isCorrect = userAttempt?.is_correct;

                    return (
                      <TableRow key={question.id}>
                        <TableCell className="font-medium">
                          <div className="flex items-start gap-2">
                            <span className="text-muted-foreground">
                              {index + 1}.
                            </span>
                            <span className="flex-1">
                              {question.question_text}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">
                          {selectedAnswer ? (
                            <Badge variant="secondary">{selectedAnswer}</Badge>
                          ) : (
                            <Badge variant="outline">{t("skipped")}</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="default">
                            {question.correct_answer}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          {isCorrect === true && (
                            <CheckCircle2 className="mx-auto h-5 w-5 text-green-500" />
                          )}
                          {isCorrect === false && (
                            <XCircle className="mx-auto h-5 w-5 text-red-500" />
                          )}
                          {isCorrect === null || isCorrect === undefined ? (
                            <MinusCircle className="mx-auto h-5 w-5 text-muted-foreground" />
                          ) : null}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            {included_questions.length === 0 && (
              <div className="mt-4 text-center text-muted-foreground">
                {t("noQuestionsFound")}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// InfoCard and Skeleton components remain unchanged.
const InfoCard = ({
  title,
  value,
  Icon,
}: {
  title: string;
  value: string | number;
  Icon?: React.ElementType;
}) => (
  <div className="flex items-center space-x-3 rounded-lg border bg-card p-4 rtl:space-x-reverse">
    {Icon && (
      <div className="rounded-md bg-muted p-2">
        <Icon className="h-5 w-5 text-muted-foreground" />
      </div>
    )}
    <div>
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  </div>
);

const DetailsPageSkeleton = () => (
  <div className="container mx-auto space-y-6 p-4 md:p-6 lg:p-8">
    <Card>
      <CardHeader>
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-md" />
          <div className="space-y-2">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        </div>
        <Skeleton className="h-px w-full" />
        <div className="space-y-4">
          <Skeleton className="h-6 w-40" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {[...Array(2)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-lg" />
            ))}
          </div>
        </div>
        <Skeleton className="h-px w-full" />
        <div className="space-y-4">
          <Skeleton className="h-6 w-48" />
          <div className="rounded-md border">
            <div className="space-y-px p-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
);

export default LevelAssessmentDetailsPage;
