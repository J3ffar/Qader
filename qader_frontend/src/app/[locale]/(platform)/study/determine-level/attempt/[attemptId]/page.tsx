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
  Clock,
  XCircle,
  Loader2,
  Send,
  HelpCircle,
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
import { queryKeys } from "@/constants/queryKeys";
import Image from "next/image";
import { QuestionRenderer } from "@/components/shared/QuestionRenderer";
import { RichContentViewer } from "@/components/shared/RichContentViewer";

type OptionKey = "A" | "B" | "C" | "D";
interface UserSelections {
  [questionId: number]: OptionKey | undefined;
}

const TEST_DURATION_SECONDS = 30 * 60;

const LevelAssessmentAttemptPage = () => {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const t = useTranslations("Study.determineLevel.quiz");
  const tCommon = useTranslations("Common");
  const locale = params.locale as string;
  const attemptId = params.attemptId as string;

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userSelections, setUserSelections] = useState<UserSelections>({});
  const [timeLeft, setTimeLeft] = useState(TEST_DURATION_SECONDS);
  const [isTimeUp, setIsTimeUp] = useState(false);
  const [direction, setDirection] = useState<"ltr" | "rtl">("ltr");

  useEffect(() => {
    setDirection(document.documentElement.dir as "ltr" | "rtl");
  }, []);

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

  useEffect(() => {
    if (attemptDetails && attemptDetails.status !== "started") {
      router.replace(PATHS.STUDY.DETERMINE_LEVEL.SCORE(attemptId));
    }
  }, [attemptDetails, router, attemptId]);

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

  useEffect(() => {
    if (
      isLoadingAttempt ||
      !attemptDetails ||
      attemptDetails.status === "completed" ||
      isTimeUp
    ) {
      return;
    }
    if (timeLeft <= 0) {
      setIsTimeUp(true);
      toast.warning(t("timeOver"), { duration: 5000 });
      handleCompleteTest(true);
      return;
    }
    const timerId = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    return () => clearInterval(timerId);
  }, [timeLeft, isLoadingAttempt, attemptDetails, isTimeUp]);

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(
      2,
      "0"
    )}`;
  };

  const submitAnswerMutation = useMutation({
    mutationFn: (payload: SubmitAnswerPayload & { attemptId: string }) =>
      submitAnswer(payload.attemptId, {
        question_id: payload.question_id,
        selected_answer: payload.selected_answer,
      }),
    onError: (error: any, variables) => {
      const errorMsg = getApiErrorMessage(error, tCommon("errors.generic"));
      toast.error(
        t("api.answerSubmitError", {
          questionId: variables.question_id,
          error: errorMsg,
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
    onSuccess: (data, attemptId) => {
      toast.success(t("api.testCompletedSuccess"));
      queryClient.setQueryData(
        queryKeys.tests.completionResult(attemptId),
        data
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.tests.lists(),
      });
      router.push(PATHS.STUDY.DETERMINE_LEVEL.SCORE(attemptId));
    },
    onError: (error: any) => {
      const errorMsg = getApiErrorMessage(error, tCommon("errors.generic"));
      toast.error(t("api.testCompleteError", { error: errorMsg }));
    },
  });

  const cancelTestMutation = useMutation({
    mutationFn: cancelTestAttempt,
    onSuccess: () => {
      toast.success(t("api.testCancelledSuccess"));
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.lists() });
      queryClient.removeQueries({
        queryKey: queryKeys.tests.detail(attemptId),
      });
      router.push(PATHS.STUDY.DETERMINE_LEVEL.LIST);
    },
    onError: (error: any) => {
      const errorMsg = getApiErrorMessage(error, tCommon("errors.generic"));
      toast.error(t("api.testCancelError", { error: errorMsg }));
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

  const handleCompleteTest = async (autoSubmittedDueToTimeUp = false) => {
    if (attemptDetails?.status !== "started") return;

    if (
      currentQuestion &&
      userSelections[currentQuestion.id] &&
      !autoSubmittedDueToTimeUp
    ) {
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
        <Alert variant="default" className="max-w-md">
          <AlertTriangle className="h-5 w-5" />
          <AlertTitle>{t("noQuestionsTitle")}</AlertTitle>
          <AlertDescription>{t("noQuestionsDescription")}</AlertDescription>
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
          {tCommon("backToList")}
        </Button>
      </div>
    );
  }

  const progressValue = (currentQuestionIndex / questions.length) * 100;

  return (
    <div className="container mx-auto flex flex-col items-center p-4 md:p-6 lg:p-8">
      <Card className="w-full max-w-3xl shadow-xl dark:bg-[#0B1739]">
        <CardHeader dir={locale==="en"?"ltr":"rtl"} className="pb-4">
          <div className="mb-3 flex items-center justify-between">
            <CardTitle className="text-xl md:text-2xl">{t("title")}</CardTitle>
            <ConfirmationDialog
              triggerButton={
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-destructive"
                >
                  <XCircle className="me-1.5 h-4 w-4 rtl:me-0 rtl:ms-1.5" />
                  {t("endTest")}
                </Button>
              }
              title={t("cancelDialog.title")}
              description={t("cancelDialog.description")}
              confirmActionText={t("cancelDialog.confirmButton")}
              cancelActionText={tCommon("no")}
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
            <div className="flex items-center">
              <Clock className="me-1.5 h-4 w-4 rtl:me-0 rtl:ms-1.5" />
              <span>{formatTime(timeLeft)}</span>
            </div>
          </div>
          <Progress value={progressValue} className="mt-2 h-2 w-full" />
        </CardHeader>

        <CardContent className="min-h-[250px] py-6">
          <QuestionRenderer
            questionText={currentQuestion.question_text}
            imageUrl={currentQuestion.image}
          />

          {currentQuestion.options ? (
            <RadioGroup
              value={userSelections[currentQuestion.id] || ""}
              onValueChange={(value: string) =>
                handleSelectAnswer(value as OptionKey)
              }
              className="space-y-3 mt-8"
              dir={direction}
            >
              {Object.entries(currentQuestion.options).map(([key, text]) => {
                const optionKey = key as OptionKey;
                return (
                  <Label
                    key={optionKey}
                    htmlFor={`${currentQuestion.id}-${optionKey}`}
                    className="has-[input:checked]:border-primary has-[input:checked]:bg-primary has-[input-checked]:text-primary-foreground flex cursor-pointer items-center space-x-3 rounded-md border p-3 text-base transition-colors hover:bg-accent rtl:space-x-reverse"
                  >
                    <RadioGroupItem
                      value={optionKey}
                      id={`${currentQuestion.id}-${optionKey}`}
                      className="border-primary text-primary"
                    />
                    <RichContentViewer
                      htmlContent={text}
                      className="prose dark:prose-invert max-w-none flex-1"
                    />
                  </Label>
                );
              })}
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

        <CardFooter dir={locale==="en"?"ltr":"rtl"} className="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row">
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
              <ChevronRight className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
            ) : (
              <ChevronLeft className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
            )}
            {t("previous")}
          </Button>
          {currentQuestionIndex < questions.length - 1 ? (
            <Button
              onClick={handleNext}
              disabled={
                !userSelections[currentQuestion.id] ||
                !currentQuestion.options ||
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
                  <Loader2 className="me-2 h-4 w-4 animate-spin rtl:me-0 rtl:ms-2" />
                )}
              {t("next")}
              {locale === "ar" ? (
                <ChevronLeft className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
              ) : (
                <ChevronRight className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
              )}
            </Button>
          ) : (
            <ConfirmationDialog
              triggerButton={
                <Button
                  className="w-full sm:w-auto"
                  disabled={
                    !userSelections[currentQuestion.id] ||
                    !currentQuestion.options ||
                    completeTestMutation.isPending ||
                    cancelTestMutation.isPending ||
                    (submitAnswerMutation.isPending &&
                      submitAnswerMutation.variables?.question_id ===
                        currentQuestion?.id)
                  }
                >
                  {completeTestMutation.isPending && (
                    <Loader2 className="me-2 h-4 w-4 animate-spin rtl:me-0 rtl:ms-2" />
                  )}
                  <Send className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
                  {t("submitAnswers")}
                </Button>
              }
              title={t("completeDialog.title")}
              description={t("completeDialog.description")}
              confirmActionText={t("completeDialog.confirmButton")}
              cancelActionText={tCommon("no")}
              onConfirm={() => handleCompleteTest(false)}
              isConfirming={completeTestMutation.isPending}
              confirmButtonVariant="default"
            />
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

export default LevelAssessmentAttemptPage;
