"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  XCircle,
  Loader2,
  Send,
  HelpCircle,
  BookOpenCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

import {
  getTestAttemptDetails,
  submitAnswer,
  completeTestAttempt,
  cancelTestAttempt,
} from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import type {
  UserTestAttemptDetail,
  UnifiedQuestion,
  SubmitAnswerPayload,
  UserTestAttemptCompletionResponse,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { cn } from "@/lib/utils";
import { queryKeys } from "@/constants/queryKeys";

type OptionKey = "A" | "B" | "C" | "D";
interface UserSelections {
  [questionId: number]: OptionKey | undefined;
}

const TestAttemptPage = () => {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const t = useTranslations("Study.tests.quiz");
  const tCommon = useTranslations("Common");

  const locale = params.locale as string;
  const attemptId = params.attemptId as string;

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userSelections, setUserSelections] = useState<UserSelections>({});

  const {
    data: attemptDetails,
    isLoading: isLoadingAttempt,
    error: attemptError,
    isSuccess,
  } = useQuery<UserTestAttemptDetail, Error>({
    queryKey: queryKeys.tests.detail(attemptId),
    queryFn: () => getTestAttemptDetails(attemptId),
    enabled: !!attemptId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Redirect if the test is already completed
  useEffect(() => {
    if (attemptDetails && attemptDetails.status !== "started") {
      router.replace(PATHS.STUDY.TESTS.SCORE(attemptId));
    }
  }, [attemptDetails, router, attemptId]);

  // Pre-fill answers if user is resuming a test
  useEffect(() => {
    if (isSuccess && attemptDetails) {
      const initialSelections: UserSelections = {};
      attemptDetails.attempted_questions?.forEach((aq) => {
        if (aq.selected_answer) {
          initialSelections[aq.question_id] = aq.selected_answer;
        }
      });
      setUserSelections(initialSelections);
    }
  }, [isSuccess, attemptDetails]);

  const questions: UnifiedQuestion[] = useMemo(
    () => attemptDetails?.included_questions || [],
    [attemptDetails]
  );
  const currentQuestion: UnifiedQuestion | undefined =
    questions[currentQuestionIndex];

  const submitAnswerMutation = useMutation({
    mutationFn: (payload: SubmitAnswerPayload & { attemptId: string }) =>
      submitAnswer(payload.attemptId, {
        question_id: payload.question_id,
        selected_answer: payload.selected_answer,
      }),
    onError: (error: any, variables) => {
      toast.error(
        t("api.answerSubmitError", {
          questionId: variables.question_id,
          error: getApiErrorMessage(error, tCommon("errors.generic")),
        })
      );
    },
  });

  const completeTestMutation = useMutation<
    UserTestAttemptCompletionResponse,
    Error,
    string
  >({
    mutationFn: completeTestAttempt,
    onSuccess: (data, completedAttemptId) => {
      toast.success(t("api.testCompletedSuccess"));
      queryClient.setQueryData(
        queryKeys.tests.completionResult(attemptId),
        data
      );
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
      router.push(PATHS.STUDY.TESTS.SCORE(completedAttemptId));
    },
    onError: (error: any) => {
      toast.error(
        t("api.testCompleteError", {
          error: getApiErrorMessage(error, tCommon("errors.generic")),
        })
      );
    },
  });

  const cancelTestMutation = useMutation<void, Error, string>({
    mutationFn: cancelTestAttempt,
    onSuccess: () => {
      toast.info(t("api.testCancelledSuccess"));
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
      queryClient.removeQueries({
        queryKey: queryKeys.tests.detail(attemptId),
      });
      router.push(PATHS.STUDY.TESTS.LIST);
    },
    onError: (error: any) => {
      toast.error(
        t("api.testCancelError", {
          error: getApiErrorMessage(error, tCommon("errors.generic")),
        })
      );
    },
  });

  const handleSelectAnswer = (selectedOption: OptionKey) => {
    if (currentQuestion) {
      setUserSelections((prev) => ({
        ...prev,
        [currentQuestion.id]: selectedOption,
      }));
    }
  };

  const submitCurrentAnswer = async (
    questionId: number,
    selectedAnswer: OptionKey | undefined
  ) => {
    if (selectedAnswer && attemptDetails?.status === "started") {
      await submitAnswerMutation.mutateAsync({
        attemptId,
        question_id: questionId,
        selected_answer: selectedAnswer,
      });
    }
  };

  const handleNext = async () => {
    if (currentQuestion) {
      await submitCurrentAnswer(
        currentQuestion.id,
        userSelections[currentQuestion.id]
      );
    }
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else {
      handleCompleteTest();
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  const handleCompleteTest = async () => {
    if (attemptDetails?.status !== "started") return;

    if (currentQuestion && userSelections[currentQuestion.id]) {
      await submitCurrentAnswer(
        currentQuestion.id,
        userSelections[currentQuestion.id]
      );
    }
    completeTestMutation.mutate(attemptId);
  };

  const handleCancelTest = () => {
    cancelTestMutation.mutate(attemptId);
  };

  // RENDER LOGIC
  if (isLoadingAttempt) return <QuizPageSkeleton />;

  if (attemptError || !attemptDetails) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert variant="destructive" className="max-w-md">
          <AlertTriangle className="h-5 w-5" />
          <AlertTitle>{tCommon("errors.fetchFailedTitle")}</AlertTitle>
          <AlertDescription>
            {getApiErrorMessage(attemptError, tCommon("errors.generic"))}
          </AlertDescription>
        </Alert>
        <Button
          onClick={() => router.back()}
          variant="outline"
          className="mt-6"
        >
          {locale === "ar" ? (
            <ArrowRight className="me-2 h-4 w-4" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4" />
          )}
          {tCommon("back")}
        </Button>
      </div>
    );
  }

  if (attemptDetails.status !== "started") {
    return <QuizPageSkeleton message={t("testAlreadyCompletedRedirecting")} />;
  }

  if (!currentQuestion) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert className="max-w-md">
          <AlertTriangle className="h-5 w-5" />
          <AlertTitle>{t("noQuestionsTitle")}</AlertTitle>
          <AlertDescription>{t("noQuestionsDescription")}</AlertDescription>
        </Alert>
        <Button
          onClick={() => router.push(PATHS.STUDY.TESTS.LIST)}
          variant="outline"
          className="mt-6"
        >
          {locale === "ar" ? (
            <ArrowRight className="me-2 h-4 w-4" />
          ) : (
            <ArrowLeft className="me-2 h-4 w-4" />
          )}
          {tCommon("backToList")}
        </Button>
      </div>
    );
  }

  const progressValue = ((currentQuestionIndex + 1) / questions.length) * 100;
  const isLastQuestion = currentQuestionIndex === questions.length - 1;
  const pageTitle =
    attemptDetails.test_type === "simulation"
      ? t("simulationTitle")
      : t("title");

  return (
    <div className="container mx-auto flex flex-col items-center p-4 md:p-6 lg:p-8">
      <Card className="w-full max-w-4xl shadow-xl">
        <CardHeader className="pb-4">
          <div className="mb-3 flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-xl md:text-2xl">
              <BookOpenCheck className="h-6 w-6 text-primary" />
              {pageTitle}
            </CardTitle>
            <ConfirmationDialog
              triggerButton={
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-destructive"
                >
                  <XCircle className="me-1.5 h-4 w-4" />
                  {t("endTest")}
                </Button>
              }
              title={t("cancelDialog.title")}
              description={t("cancelDialog.description")}
              confirmActionText={t("cancelDialog.confirmButton")}
              onConfirm={handleCancelTest}
              isConfirming={cancelTestMutation.isPending}
              confirmButtonVariant="destructive"
            />
          </div>
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {t("question")} {currentQuestionIndex + 1} {t("outOf")}{" "}
              {questions.length}
            </span>
          </div>
          <Progress value={progressValue} className="mt-2 h-2 w-full" />
        </CardHeader>

        <CardContent className="min-h-[300px] py-6">
          <h2
            className="mb-6 text-right text-lg font-semibold leading-relaxed rtl:text-right md:text-xl"
            dir="auto"
          >
            {currentQuestion.question_text}
          </h2>

          {currentQuestion.options ? (
            <RadioGroup
              value={userSelections[currentQuestion.id] || ""}
              onValueChange={(value: string) =>
                handleSelectAnswer(value as OptionKey)
              }
              className="space-y-3"
              dir="ltr" // Keep radio group LTR for consistency, label text will still follow page direction
            >
              {Object.entries(currentQuestion.options).map(([key, text]) => (
                <Label
                  key={key}
                  htmlFor={`${currentQuestion.id}-${key}`}
                  className={cn(
                    "flex cursor-pointer items-center space-x-3 rounded-md border p-4 text-base transition-colors hover:bg-accent rtl:space-x-reverse",
                    "has-[input:checked]:border-primary has-[input:checked]:bg-primary/10 has-[input:checked]:ring-2 has-[input:checked]:ring-primary"
                  )}
                >
                  <RadioGroupItem
                    value={key}
                    id={`${currentQuestion.id}-${key}`}
                    className="border-muted-foreground"
                  />
                  <span className="flex-1" dir="auto">
                    {text}
                  </span>
                </Label>
              ))}
            </RadioGroup>
          ) : (
            <Alert variant="destructive">
              <HelpCircle className="h-5 w-5" />
              <AlertTitle>{t("questionLoadError.title")}</AlertTitle>
              <AlertDescription>
                {t("questionLoadError.description", {
                  questionId: currentQuestion.id,
                })}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>

        <CardFooter className="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={
              currentQuestionIndex === 0 ||
              completeTestMutation.isPending ||
              cancelTestMutation.isPending
            }
            className="w-full sm:w-auto"
          >
            {locale === "ar" ? (
              <ArrowRight className="me-2 h-5 w-5" />
            ) : (
              <ArrowLeft className="me-2 h-5 w-5" />
            )}
            {t("previous")}
          </Button>

          {isLastQuestion ? (
            <ConfirmationDialog
              triggerButton={
                <Button
                  className="w-full sm:w-auto"
                  disabled={
                    !userSelections[currentQuestion.id] ||
                    completeTestMutation.isPending ||
                    cancelTestMutation.isPending
                  }
                >
                  {completeTestMutation.isPending && (
                    <Loader2 className="me-2 h-4 w-4 animate-spin" />
                  )}
                  <Send className="me-2 h-5 w-5" />
                  {t("submitAnswers")}
                </Button>
              }
              title={t("completeDialog.title")}
              description={t("completeDialog.description")}
              confirmActionText={t("completeDialog.confirmButton")}
              onConfirm={() => handleCompleteTest()}
              isConfirming={completeTestMutation.isPending}
            />
          ) : (
            <Button
              onClick={handleNext}
              disabled={
                !userSelections[currentQuestion.id] ||
                completeTestMutation.isPending ||
                cancelTestMutation.isPending ||
                (submitAnswerMutation.isPending &&
                  submitAnswerMutation.variables?.question_id ===
                    currentQuestion?.id)
              }
              className="w-full sm:w-auto"
            >
              {submitAnswerMutation.isPending &&
                submitAnswerMutation.variables?.question_id ===
                  currentQuestion?.id && (
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                )}
              {t("next")}
              {locale === "ar" ? (
                <ChevronLeft className="ms-2 h-5 w-5" />
              ) : (
                <ChevronRight className="ms-2 h-5 w-5" />
              )}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
};

const QuizPageSkeleton = ({ message }: { message?: string }) => {
  return (
    <div className="container mx-auto flex flex-col items-center p-4 md:p-6 lg:p-8">
      <Card className="w-full max-w-3xl">
        <CardHeader className="pb-4">
          <div className="mb-3 flex items-center justify-between">
            <Skeleton className="h-7 w-1/2" />
            <Skeleton className="h-8 w-24" />
          </div>
          <div className="flex items-center justify-between text-sm">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="h-5 w-1/4" />
          </div>
          <Skeleton className="mt-2 h-2 w-full" />
        </CardHeader>
        <CardContent className="min-h-[250px] py-6">
          {message ? (
            <p className="text-center text-muted-foreground">{message}</p>
          ) : (
            <>
              <Skeleton className="mb-6 h-6 w-3/4" />
              <div className="space-y-4">
                {[...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className="flex items-center space-x-3 rtl:space-x-reverse"
                  >
                    <Skeleton className="h-5 w-5 rounded-full" />
                    <Skeleton className="h-10 flex-1 rounded-md" />
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
        <CardFooter className="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row">
          <Skeleton className="h-10 w-full sm:w-28" />
          <Skeleton className="h-10 w-full sm:w-28" />
        </CardFooter>
      </Card>
    </div>
  );
};

export default TestAttemptPage;
