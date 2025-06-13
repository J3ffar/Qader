"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { BookOpen, ChevronRight, Lightbulb, Loader2, X } from "lucide-react";

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
import { Skeleton } from "@/components/ui/skeleton";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";
import {
  getTestAttemptDetails,
  completeTestAttempt,
  submitAnswer,
  getHintForQuestion,
  revealExplanationForQuestion,
} from "@/services/study.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { PATHS } from "@/constants/paths";
import type {
  UnifiedQuestion,
  SubmitAnswerPayload,
} from "@/types/api/study.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { cn } from "@/lib/utils";

type OptionKey = "A" | "B" | "C" | "D";

const TraditionalPracticePage = () => {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  // Using the correct namespace for this page's translations
  const t = useTranslations("Study.traditionalLearning.session");
  const tCommon = useTranslations("Common");
  const attemptId = params.attemptId as string;

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<OptionKey | null>(null);
  const [answeredStates, setAnsweredStates] = useState<
    Record<number, { isCorrect: boolean; selected: OptionKey }>
  >({});
  const [sessionStats, setSessionStats] = useState({
    correct: 0,
    incorrect: 0,
    points: 0,
  });

  const {
    data: attemptDetails,
    isLoading,
    error,
  } = useQuery({
    queryKey: [QUERY_KEYS.USER_TEST_ATTEMPT_DETAIL, attemptId],
    queryFn: () => getTestAttemptDetails(attemptId),
    enabled: !!attemptId,
    refetchOnWindowFocus: false,
  });

  const questions = useMemo(
    () => attemptDetails?.included_questions || [],
    [attemptDetails]
  );
  const currentQuestion = useMemo(
    () => questions[currentQuestionIndex],
    [questions, currentQuestionIndex]
  );

  useEffect(() => {
    setSelectedOption(null);
  }, [currentQuestionIndex]);

  const submitAnswerMutation = useMutation({
    mutationFn: (payload: { attemptId: string; data: SubmitAnswerPayload }) =>
      submitAnswer(payload.attemptId, payload.data),
    onSuccess: (data) => {
      const isCorrect = data.question.user_answer_details?.is_correct ?? false;
      const correctChoiceText =
        data.question.options[data.question.correct_answer];

      toast[isCorrect ? "success" : "error"](
        isCorrect
          ? t("correct")
          : `${t("incorrect")} ${t("correctAnswerWas")} ${correctChoiceText}`
      );

      setAnsweredStates((prev) => ({
        ...prev,
        [data.question.id]: { isCorrect, selected: selectedOption! },
      }));
      setSessionStats((prev) => ({
        ...prev,
        correct: isCorrect ? prev.correct + 1 : prev.correct,
        incorrect: !isCorrect ? prev.incorrect + 1 : prev.incorrect,
      }));
    },
  });

  const completeSessionMutation = useMutation({
    mutationFn: completeTestAttempt,
    onSuccess: () => {
      toast.success(t("api.sessionCompletedSuccess"));
      router.push(PATHS.STUDY.HOME);
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, t("api.sessionCompleteError")));
    },
  });

  const hintMutation = useMutation({
    mutationFn: ({ questionId }: { questionId: number }) =>
      getHintForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      if (data.hint) {
        toast.success(t("api.hintSuccess"), { description: data.hint });
      } else {
        toast.info(t("api.hintNotAvailable"));
      }
    },
  });

  const explanationMutation = useMutation({
    mutationFn: ({ questionId }: { questionId: number }) =>
      revealExplanationForQuestion(attemptId, questionId),
    onSuccess: (data) => {
      if (data.explanation) {
        toast.success(t("api.explanationRevealSuccess"), {
          description: data.explanation,
          duration: 10000,
        });
      } else {
        toast.info(t("api.explanationNotAvailable"));
      }
    },
  });

  const handleNext = async () => {
    if (selectedOption && !answeredStates[currentQuestion.id]) {
      await submitAnswerMutation.mutateAsync({
        attemptId,
        data: {
          question_id: currentQuestion.id,
          selected_answer: selectedOption,
        },
      });
    }
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else {
      toast.info(t("noMoreQuestions"));
    }
  };

  if (isLoading) return <PracticePageSkeleton />;
  if (error || !currentQuestion)
    return <div>Error loading practice session.</div>;

  const progressValue = ((currentQuestionIndex + 1) / questions.length) * 100;
  const isAnswered = !!answeredStates[currentQuestion.id];

  return (
    <div className="container mx-auto p-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{t("title")}</h1>
        <ConfirmationDialog
          triggerButton={
            <Button variant="destructive" size="sm">
              <X className="me-2 h-4 w-4" />
              {t("endSession")}
            </Button>
          }
          title={t("confirmEndTitle")}
          description={t("confirmEndDescription")}
          confirmActionText={t("confirmEndButton")}
          onConfirm={() => completeSessionMutation.mutate(attemptId)}
          isConfirming={completeSessionMutation.isPending}
        />
      </div>

      <Progress value={progressValue} className="mb-6 h-2" />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Main Question Card */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              {`${t("question")} ${currentQuestionIndex + 1} ${t("outOf")} ${
                questions.length
              }`}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-6 text-lg font-semibold">
              {currentQuestion.question_text}
            </p>
            <RadioGroup
              value={selectedOption ?? ""}
              onValueChange={(v) =>
                !isAnswered && setSelectedOption(v as OptionKey)
              }
            >
              {Object.entries(currentQuestion.options).map(([key, text]) => {
                const optionKey = key as OptionKey;
                const answeredState = answeredStates[currentQuestion.id];
                const isCorrect =
                  answeredState?.isCorrect &&
                  answeredState?.selected === optionKey;
                const isIncorrect =
                  answeredState &&
                  !answeredState.isCorrect &&
                  answeredState.selected === optionKey;

                return (
                  <Label
                    key={key}
                    htmlFor={key}
                    className={cn(
                      "flex items-center space-x-3 rounded-md border p-3 transition-colors rtl:space-x-reverse",
                      !isAnswered && "cursor-pointer hover:bg-accent",
                      selectedOption === optionKey &&
                        !isAnswered &&
                        "border-primary",
                      isCorrect &&
                        "border-green-500 bg-green-100 text-green-900 dark:bg-green-900/30 dark:border-green-700",
                      isIncorrect &&
                        "border-red-500 bg-red-100 text-red-900 dark:bg-red-900/30 dark:border-red-700"
                    )}
                  >
                    <RadioGroupItem
                      value={key}
                      id={key}
                      disabled={isAnswered}
                    />
                    <span>{text}</span>
                  </Label>
                );
              })}
            </RadioGroup>
          </CardContent>
          <CardFooter>
            <Button
              onClick={handleNext}
              disabled={
                !selectedOption ||
                (currentQuestionIndex === questions.length - 1 && isAnswered)
              }
            >
              {t("next")} <ChevronRight className="ms-2 h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{t("controls.title")}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col space-y-2">
              <Button
                variant="outline"
                onClick={() =>
                  hintMutation.mutate({ questionId: currentQuestion.id })
                }
                disabled={hintMutation.isPending}
              >
                <Lightbulb className="me-2 h-4 w-4" /> {t("controls.hint")}
              </Button>
              <Button
                variant="outline"
                onClick={() =>
                  explanationMutation.mutate({ questionId: currentQuestion.id })
                }
                disabled={explanationMutation.isPending}
              >
                <BookOpen className="me-2 h-4 w-4" />{" "}
                {t("controls.showSolution")}
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>{t("sessionStatsTitle")}</CardTitle>
            </CardHeader>
            <CardContent className="flex justify-around text-center">
              <div>
                <p className="text-2xl font-bold text-green-600">
                  {sessionStats.correct}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t("correctAnswers")}
                </p>
              </div>
              <div>
                <p className="text-2xl font-bold text-red-600">
                  {sessionStats.incorrect}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t("incorrectAnswers")}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const PracticePageSkeleton = () => (
  // Skeleton remains unchanged
  <div className="container mx-auto animate-pulse p-4">
    <div className="mb-4 h-8 w-1/3 rounded bg-muted"></div>
    <div className="mb-6 h-2 w-full rounded bg-muted"></div>
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <div className="h-8 w-1/4 rounded bg-muted"></div>
        <div className="h-20 w-full rounded bg-muted"></div>
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-12 w-full rounded bg-muted"></div>
          ))}
        </div>
      </div>
      <div className="space-y-6">
        <div className="h-32 w-full rounded bg-muted"></div>
        <div className="h-32 w-full rounded bg-muted"></div>
      </div>
    </div>
  </div>
);

export default TraditionalPracticePage;
