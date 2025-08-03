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
import { StarButton } from "@/components/shared/StarButton";

import {
  resumeTestAttempt,
  submitAnswer,
  completeTestAttempt,
  cancelTestAttempt,
} from "@/services/study.service";
import { PATHS } from "@/constants/paths";
import type {
  // MODIFIED: Using new types
  UserTestAttemptResume,
  SubmitAnswerResponse,
  UnifiedQuestion,
  SubmitAnswerPayload,
  UserTestAttemptCompletionResponse,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { cn } from "@/lib/utils";
import { queryKeys } from "@/constants/queryKeys";
import { RichContentViewer } from "@/components/shared/RichContentViewer";
import { QuestionRenderer } from "@/components/shared/QuestionRenderer";

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
  const [localStarred, setLocalStarred] = useState(false);
  const [direction, setDirection] = useState<"ltr" | "rtl">("ltr");
  const [isReady, setIsReady] = useState(false); // NEW: State to prevent premature rendering

  // NEW: State for time tracking per question
  const [questionStartTime, setQuestionStartTime] = useState<number>(0);

  useEffect(() => {
    setDirection(document.documentElement.dir as "ltr" | "rtl");
  }, []);

  // MODIFIED: Use the new `resumeTestAttempt` service function
  const {
    data: attemptData,
    isLoading: isLoadingAttempt,
    error: attemptError,
    isSuccess,
  } = useQuery<UserTestAttemptResume, Error>({
    // Using a distinct key for resume is cleaner
    queryKey: queryKeys.tests.resume(attemptId),
    queryFn: () => resumeTestAttempt(attemptId),
    enabled: !!attemptId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Redirect if the test is already completed
  // Note: The `resume` endpoint will likely fail for completed tests, which attemptError will catch.
  // This useEffect is a good fallback.
  useEffect(() => {
    if (attemptError) {
      // If resume fails, it might be completed. Redirect to score page.
      // A more robust solution would check the error status code (e.g., 400).
      toast.error(t("api.resumeErrorRedirecting"));
      router.replace(PATHS.STUDY.TESTS.SCORE(attemptId));
    }
  }, [attemptError, router, attemptId, t]);

  const questions: UnifiedQuestion[] = useMemo(
    () => attemptData?.questions || [],
    [attemptData]
  );

  // MODIFIED: Enhanced useEffect to handle resume logic
  useEffect(() => {
    if (isSuccess && attemptData) {
      if (
        attemptData.total_questions > 0 &&
        attemptData.total_questions === attemptData.answered_question_count
      ) {
        handleCompleteTest(true); // Force complete if all questions are answered
        return;
      }

      const initialSelections: UserSelections = {};
      let firstUnansweredIndex = -1;

      questions.forEach((q, index) => {
        if (q.user_answer_details?.selected_choice) {
          initialSelections[q.id] = q.user_answer_details.selected_choice;
        } else if (firstUnansweredIndex === -1) {
          firstUnansweredIndex = index;
        }
      });

      setUserSelections(initialSelections);
      setCurrentQuestionIndex(
        firstUnansweredIndex !== -1 ? firstUnansweredIndex : 0
      );
      setIsReady(true); // Mark component as ready to render
    }
  }, [isSuccess, attemptData, questions]);

  const currentQuestion: UnifiedQuestion | undefined =
    questions[currentQuestionIndex];

  // MODIFIED: useEffect to start the timer and update star status
  useEffect(() => {
    if (isReady && currentQuestion) {
      setQuestionStartTime(Date.now());
      setLocalStarred(currentQuestion.is_starred);
    }
  }, [currentQuestionIndex, isReady, currentQuestion]);

  // MODIFIED: Updated submitAnswerMutation with optimistic update
  const submitAnswerMutation = useMutation({
    mutationFn: (payload: SubmitAnswerPayload & { attemptId: string }) =>
      submitAnswer(payload.attemptId, payload),

    onSuccess: (data: SubmitAnswerResponse, variables) => {
      const queryKey = queryKeys.tests.resume(variables.attemptId);
      queryClient.setQueryData<UserTestAttemptResume>(queryKey, (oldData) => {
        if (!oldData) return undefined;
        const wasAlreadyAnswered =
          oldData.questions.find((q) => q.id === data.question.id)
            ?.user_answer_details !== null;
        const newQuestions = oldData.questions.map((q) =>
          q.id === data.question.id ? data.question : q
        );
        return {
          ...oldData,
          questions: newQuestions,
          answered_question_count: wasAlreadyAnswered
            ? oldData.answered_question_count
            : oldData.answered_question_count + 1,
        };
      });
    },
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
    if (selectedAnswer) {
      const timeTakenSeconds = Math.round(
        (Date.now() - questionStartTime) / 1000
      );
      await submitAnswerMutation.mutateAsync({
        attemptId,
        question_id: questionId,
        selected_answer: selectedAnswer,
        time_taken_seconds: timeTakenSeconds,
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

  const handleCompleteTest = async (forceComplete = false) => {
    if (
      !forceComplete &&
      currentQuestion &&
      userSelections[currentQuestion.id]
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

  // RENDER LOGIC
  if (isLoadingAttempt || !isReady) return <QuizPageSkeleton />;

  // The previous error handling for `attemptDetails` is now covered by the `attemptError` effect
  if (attemptError) {
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
  if (!currentQuestion) {
    return (
      <div className="container mx-auto flex min-h-[calc(100vh-200px)] flex-col items-center justify-center p-6">
        <Alert className="max-w-md">
          <HelpCircle className="h-5 w-5" />
          <AlertTitle>{t("noQuestionsTitle")}</AlertTitle>
          <AlertDescription>{t("noQuestionsDescription")}</AlertDescription>
        </Alert>
        <Button
          onClick={() => router.push(PATHS.STUDY.TESTS.LIST)}
          variant="outline"
          className="mt-6"
        >
          {direction === "rtl" ? (
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
  // const pageTitle =
  //   attemptData?.test_type === "simulation" // Use attemptData for test_type
  //     ? t("simulationTitle")
  //     : t("title");

  return (
    <div className="container mx-auto flex flex-col items-center p-4 md:p-6 lg:p-8">
      <Card className="w-full max-w-4xl shadow-xl dark:bg-[#0B1739]">
        <CardHeader dir={direction} className="pb-4">
          <div className="mb-3 flex items-center justify-between">
            {/* <CardTitle className="flex items-center gap-2 text-xl md:text-2xl">
              <BookOpenCheck className="h-6 w-6 text-primary" />
              {pageTitle}
            </CardTitle> */}
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

        <CardContent dir={direction} className="min-h-[300px] py-6">
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-1">
              <QuestionRenderer
                questionText={currentQuestion.question_text}
                imageUrl={currentQuestion.image}
              />
            </div>
            <div className="flex-shrink-0 pt-2">
              <StarButton
                questionId={currentQuestion.id}
                isStarred={localStarred}
                onStarChange={(newState) => setLocalStarred(newState)}
                disabled={false}
                attemptId={attemptId}
              />
            </div>
          </div>

          {currentQuestion.options ? (
            <RadioGroup
              value={userSelections[currentQuestion.id] || ""}
              onValueChange={(value: string) =>
                handleSelectAnswer(value as OptionKey)
              }
              className="space-y-3 mt-8"
              // MODIFIED: Use dynamic direction
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

        <CardFooter
          dir={direction}
          className="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row"
        >
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
            {direction === "rtl" ? (
              <ArrowRight className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
            ) : (
              <ArrowLeft className="me-2 h-5 w-5 rtl:me-0 rtl:ms-2" />
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
                    cancelTestMutation.isPending ||
                    (submitAnswerMutation.isPending &&
                      submitAnswerMutation.variables?.question_id ===
                        currentQuestion.id)
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
                    currentQuestion.id)
              }
              className="w-full sm:w-auto"
            >
              {submitAnswerMutation.isPending &&
                submitAnswerMutation.variables?.question_id ===
                  currentQuestion.id && (
                  <Loader2 className="me-2 h-4 w-4 animate-spin rtl:me-0 rtl:ms-2" />
                )}
              {t("next")}
              {direction === "rtl" ? (
                <ChevronLeft className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
              ) : (
                <ChevronRight className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
              )}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
};

const QuizPageSkeleton = ({ message }: { message?: string }) => {
  // ... Skeleton component remains unchanged
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
