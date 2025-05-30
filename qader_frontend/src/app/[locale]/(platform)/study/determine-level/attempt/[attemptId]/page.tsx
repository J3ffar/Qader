// src/app/[locale]/(platform)/study/determine-level/attempt/[attemptId]/page.tsx
"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  XCircle,
  Loader2,
  Send,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
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
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import type {
  QuestionOptionKey,
  QuestionSchema,
  SubmitAnswerPayload,
  UserTestAttemptDetail,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { cn } from "@/lib/utils";

const TEST_DURATION_SECONDS = 30 * 60; // 30 minutes, adjust as needed or fetch from backend if dynamic

interface UserSelections {
  [questionId: number]: keyof QuestionOptionKey | undefined;
}

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
  const [timeLeft, setTimeLeft] = useState(TEST_DURATION_SECONDS); // Or fetch from attemptDetails if available
  const [isTimeUp, setIsTimeUp] = useState(false);

  const {
    data: attemptDetails, // Type will be UserTestAttemptDetail | undefined
    isLoading: isLoadingAttempt,
    error: attemptError,
    isSuccess, // Useful for useEffect
  } = useQuery<UserTestAttemptDetail, Error, UserTestAttemptDetail, string[]>({
    // Explicitly type query
    queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_DETAIL, attemptId],
    queryFn: () => getTestAttemptDetails(attemptId),
    enabled: !!attemptId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Handle onSuccess logic using useEffect
  useEffect(() => {
    if (isSuccess && attemptDetails) {
      // Check isSuccess and if data exists
      const initialSelections: UserSelections = {};
      // Type `aq` by using the type from UserTestAttemptDetail
      attemptDetails.attempted_questions?.forEach(
        (aq: UserTestAttemptDetail["attempted_questions"][number]) => {
          if (aq.selected_answer) {
            initialSelections[aq.question_id] = aq.selected_answer;
          }
        }
      );
      console.log(attemptDetails);
      setUserSelections(initialSelections);
      setCurrentQuestionIndex(0); // Or logic to find last unanswered question
    }
  }, [isSuccess, attemptDetails]);

  const questions: QuestionSchema[] = useMemo(
    () => attemptDetails?.included_questions || [],
    [attemptDetails]
  );

  const currentQuestion: QuestionSchema | undefined =
    questions[currentQuestionIndex];

  // Timer Logic
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
      // Automatically submit the test when time is up
      handleCompleteTest(true);
      return;
    }
    const timerId = setInterval(() => {
      setTimeLeft((prevTime) => prevTime - 1);
    }, 1000);
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
    onSuccess: (data, variables) => {
      // Optionally show a subtle feedback, but usually not needed per question
      // console.log(`Answer for Q${variables.question_id} submitted.`);
    },
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

  const completeTestMutation = useMutation({
    mutationFn: completeTestAttempt,
    onSuccess: (data) => {
      toast.success(t("api.testCompletedSuccess"));
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPTS],
      });
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_DETAIL, attemptId],
      });
      // Navigate to score page after completion
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
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPTS],
      });
      queryClient.removeQueries({
        queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_DETAIL, attemptId],
      });
      router.push(PATHS.STUDY.DETERMINE_LEVEL.LIST);
    },
    onError: (error: any) => {
      const errorMsg = getApiErrorMessage(error, tCommon("errors.generic"));
      toast.error(t("api.testCancelError", { error: errorMsg }));
    },
  });

  const handleSelectAnswer = (selectedOption: QuestionOptionKey) => {
    if (currentQuestion) {
      const questionId = currentQuestion.id;
      setUserSelections((prevSelections: UserSelections): UserSelections => {
        return Object.assign({}, prevSelections, {
          [questionId]: selectedOption,
        }) as UserSelections; // Cast might be needed if TS still struggles
      });
    }
  };

  const optionKeys: QuestionOptionKey[] = ["A", "B", "C", "D"];

  const submitCurrentAnswer = async (
    questionId: number,
    selectedAnswer: keyof QuestionOptionKey | undefined
  ) => {
    if (
      selectedAnswer &&
      attemptDetails &&
      attemptDetails.status === "started"
    ) {
      try {
        await submitAnswerMutation.mutateAsync({
          attemptId: attemptId,
          question_id: questionId,
          selected_answer: selectedAnswer,
        });
      } catch (e) {
        // Error already handled by mutation's onError
      }
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
      // At the last question, "Next" could mean "Review before submitting" or "Complete"
      // For now, let's assume it means ready to complete
      handleCompleteTest();
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  const handleCompleteTest = async (autoSubmittedDueToTimeUp = false) => {
    if (attemptDetails?.status !== "started") {
      if (attemptDetails?.status === "completed") {
        router.push(PATHS.STUDY.DETERMINE_LEVEL.SCORE(attemptId));
      }
      return;
    }

    // Submit the last viewed answer if not yet submitted
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

    // Backend's completeTestAttempt should handle scoring all submitted answers for the attempt.
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

  if (
    attemptDetails.status === "completed" ||
    attemptDetails.status === "abandoned"
  ) {
    // Redirect to score/review page or list page
    router.replace(PATHS.STUDY.DETERMINE_LEVEL.SCORE(attemptId));
    return <QuizPageSkeleton message={t("testAlreadyCompletedRedirecting")} />; // Show skeleton while redirecting
  }

  if (!currentQuestion) {
    // This case should ideally be handled if questions array is empty after loading
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
      <Card className="w-full max-w-3xl shadow-xl">
        <CardHeader className="pb-4">
          <div className="mb-3 flex items-center justify-between">
            <CardTitle className="text-xl md:text-2xl">
              {t("title")}{" "}
              {/* {attemptDetails?.attempt_number_for_type || ""} */}
            </CardTitle>
            <ConfirmationDialog
              triggerButton={
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-destructive"
                >
                  <XCircle className="me-1.5 h-4 w-4 rtl:me-0 rtl:ms-1.5" />{" "}
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
          <h2 className="mb-6 text-right text-lg font-semibold leading-relaxed rtl:text-right md:text-xl">
            {currentQuestion.question_text}
          </h2>
          <RadioGroup
            value={userSelections[currentQuestion.id] as QuestionOptionKey}
            onValueChange={(value: string) =>
              handleSelectAnswer(value as QuestionOptionKey)
            } // Cast value
            className="space-y-3"
            dir={document.documentElement.dir as "rtl" | "ltr"}
          >
            {optionKeys.map((optionKey) => {
              // Construct the property name dynamically e.g., "option_a"
              const optionTextProperty =
                `option_${optionKey.toLowerCase()}` as keyof QuestionSchema;
              const optionText = currentQuestion[optionTextProperty] as
                | string
                | undefined;

              if (optionText === undefined) {
                // Should not happen if API is consistent
                console.warn(
                  `Option text for key ${optionKey} is undefined for question ID ${currentQuestion.id}`
                );
                return null;
              }

              return (
                <div
                  key={optionKey}
                  className="flex items-center space-x-3 rtl:space-x-reverse"
                >
                  <RadioGroupItem
                    value={optionKey}
                    id={`${currentQuestion.id}-${optionKey}`}
                    className="border-primary text-primary"
                  />
                  <Label
                    htmlFor={`${currentQuestion.id}-${optionKey}`}
                    className="has-[input:checked]:bg-primary has-[input:checked]:text-primary-foreground has-[input:checked]:border-primary flex-1 cursor-pointer rounded-md border p-3 text-base transition-colors hover:bg-accent"
                  >
                    {optionText}
                  </Label>
                </div>
              );
            })}
          </RadioGroup>
        </CardContent>

        <CardFooter className="flex flex-col items-center justify-between gap-3 pt-6 sm:flex-row">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={
              currentQuestionIndex === 0 ||
              !currentQuestion ||
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
                !currentQuestion ||
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
                    !currentQuestion ||
                    !userSelections[currentQuestion.id] ||
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
              onConfirm={() => handleCompleteTest(false)} // Explicitly false here
              isConfirming={completeTestMutation.isPending}
              confirmButtonVariant="Secondary"
            />
          )}
        </CardFooter>
      </Card>
    </div>
  );
};

const QuizPageSkeleton = ({ message }: { message?: string }) => {
  const t = useTranslations("Study.determineLevel.quiz");
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
